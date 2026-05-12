from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select

from src.api.errors.exceptions import NotFoundError
from src.core.auth import get_current_user
from src.db.session import AsyncSession, get_db_session
from src.models.document import DocumentSource
from src.models.persona import PersonaDocument, PersonaProfile
from src.models.skill import PersonaSkillMap
from src.models.user import User
from src.schemas.catalog import (
    ActivePersonaResponse,
    PersonaAttachDocumentsRequest,
    PersonaAttachDocumentsResponse,
    PersonaCreate,
    PersonaRead,
    PersonaSkillItem,
    PersonaSkillsPutRequest,
    PersonaSkillsPutResponse,
)

router = APIRouter()


@router.post(
    "",
    response_model=PersonaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create persona profile",
    description="Creates a new persona profile for the authenticated user and marks it active.",
    operation_id="personas_create",
)
async def create_persona(
    payload: PersonaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PersonaRead:
    """Create a persona for the current user, deactivating previous active personas (prototype rule)."""
    # Deactivate existing active personas (schema intends one active persona per user).
    res = await db.execute(
        select(PersonaProfile).where(PersonaProfile.user_id == current_user.id).where(PersonaProfile.is_active.is_(True))
    )
    for p in res.scalars().all():
        p.is_active = False

    persona = PersonaProfile(
        user_id=current_user.id,
        summary=payload.summary,
        attributes=payload.attributes,
        is_active=True,
        created_by=current_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(persona)
    await db.flush()
    return PersonaRead.model_validate(persona)


@router.get(
    "/active",
    response_model=ActivePersonaResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active persona",
    description="Returns the user's active persona with attached documents and skills.",
    operation_id="personas_get_active",
)
async def get_active_persona(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ActivePersonaResponse:
    """Get the current user's active persona (if any)."""
    res = await db.execute(
        select(PersonaProfile)
        .where(PersonaProfile.user_id == current_user.id)
        .where(PersonaProfile.is_active.is_(True))
        .where(PersonaProfile.deleted_at.is_(None))
        .order_by(PersonaProfile.created_at.desc())
        .limit(1)
    )
    persona = res.scalar_one_or_none()
    if persona is None:
        raise NotFoundError("Active persona not found")

    docs_res = await db.execute(select(PersonaDocument).where(PersonaDocument.persona_id == persona.id))
    document_ids = [x.document_id for x in docs_res.scalars().all()]

    skills_res = await db.execute(select(PersonaSkillMap).where(PersonaSkillMap.persona_id == persona.id))
    skills = [
        PersonaSkillItem(
            skill_id=x.skill_id,
            level=str(x.level) if x.level is not None else None,
            confidence=float(x.confidence) if x.confidence is not None else None,
            missing_evidence=bool(x.missing_evidence),
        )
        for x in skills_res.scalars().all()
    ]

    return ActivePersonaResponse(
        persona=PersonaRead.model_validate(persona),
        document_ids=document_ids,
        skills=skills,
    )


@router.post(
    "/{persona_id}/documents",
    response_model=PersonaAttachDocumentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Attach documents to persona",
    description="Links one or more documents to a persona (ownership enforced).",
    operation_id="personas_attach_documents",
)
async def attach_documents(
    persona_id: str,
    payload: PersonaAttachDocumentsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PersonaAttachDocumentsResponse:
    """Attach documents to a persona profile, enforcing that both persona and documents belong to the current user."""
    persona = await db.get(PersonaProfile, persona_id)
    if persona is None or persona.user_id != current_user.id or persona.deleted_at is not None:
        raise NotFoundError("Persona not found")

    # Verify each document belongs to user and is not deleted
    if payload.document_ids:
        docs_res = await db.execute(
            select(DocumentSource).where(DocumentSource.id.in_(payload.document_ids))  # type: ignore[arg-type]
        )
        docs = {d.id: d for d in docs_res.scalars().all()}
        for doc_id in payload.document_ids:
            d = docs.get(doc_id)
            if d is None or d.user_id != current_user.id or d.deleted_at is not None:
                raise NotFoundError(f"Document not found: {doc_id}")

    # Upsert-style: add missing links, keep existing
    existing_res = await db.execute(select(PersonaDocument).where(PersonaDocument.persona_id == persona_id))
    existing = {x.document_id for x in existing_res.scalars().all()}

    for doc_id in payload.document_ids:
        if doc_id not in existing:
            db.add(PersonaDocument(persona_id=persona_id, document_id=doc_id))

    await db.flush()
    return PersonaAttachDocumentsResponse(persona_id=persona_id, document_ids=list(payload.document_ids))


@router.put(
    "/{persona_id}/skills",
    response_model=PersonaSkillsPutResponse,
    status_code=status.HTTP_200_OK,
    summary="Set persona skills",
    description="Replaces the persona's baseline skills list (prototype).",
    operation_id="personas_put_skills",
)
async def put_persona_skills(
    persona_id: str,
    payload: PersonaSkillsPutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PersonaSkillsPutResponse:
    """Replace persona skill mappings with the provided list."""
    persona = await db.get(PersonaProfile, persona_id)
    if persona is None or persona.user_id != current_user.id or persona.deleted_at is not None:
        raise NotFoundError("Persona not found")

    # Replace all mappings for this persona (simple prototype behavior).
    await db.execute(delete(PersonaSkillMap).where(PersonaSkillMap.persona_id == persona_id))

    now = datetime.now(timezone.utc)
    for item in payload.skills:
        db.add(
            PersonaSkillMap(
                persona_id=persona_id,
                skill_id=item.skill_id,
                level=item.level,
                confidence=item.confidence,
                missing_evidence=item.missing_evidence,
                assessed_at=now,
                created_by=current_user.id,
                created_at=now,
                updated_at=now,
            )
        )

    await db.flush()
    return PersonaSkillsPutResponse(persona_id=persona_id, skills=payload.skills)
