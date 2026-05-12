from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select

from src.api.errors.exceptions import NotFoundError
from src.core.auth import get_current_user
from src.db.session import AsyncSession, get_db_session
from src.models.document import DocumentSource
from src.models.user import User
from src.schemas.catalog import DocumentCreate, DocumentRead
from src.schemas.common import Paginated

router = APIRouter()


@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create document record",
    description="Registers document metadata and storage pointer for the current user.",
    operation_id="documents_create",
)
async def create_document(
    payload: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    """Create a document metadata record for the authenticated user."""
    doc = DocumentSource(
        user_id=current_user.id,
        doc_type=payload.doc_type,
        filename=payload.filename,
        content_type=payload.content_type,
        storage_key=payload.storage_key,
        storage_url=payload.storage_url,
        uploaded_at=datetime.now(timezone.utc),
        created_by=current_user.id,
    )
    db.add(doc)
    await db.flush()
    return DocumentRead.model_validate(doc)


@router.get(
    "",
    response_model=Paginated[DocumentRead],
    status_code=status.HTTP_200_OK,
    summary="List my documents",
    description="Lists non-deleted documents belonging to the authenticated user.",
    operation_id="documents_list",
)
async def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Paginated[DocumentRead]:
    """List current user's documents with pagination."""
    items_stmt = (
        select(DocumentSource)
        .where(DocumentSource.user_id == current_user.id)
        .where(DocumentSource.deleted_at.is_(None))
        .order_by(DocumentSource.uploaded_at.desc())
        .limit(limit)
        .offset(offset)
    )
    total_stmt = (
        select(func.count())
        .select_from(DocumentSource)
        .where(DocumentSource.user_id == current_user.id)
        .where(DocumentSource.deleted_at.is_(None))
    )

    items_res = await db.execute(items_stmt)
    total_res = await db.execute(total_stmt)

    items = [DocumentRead.model_validate(x) for x in items_res.scalars().all()]
    total = int(total_res.scalar_one())

    return Paginated[DocumentRead](items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    status_code=status.HTTP_200_OK,
    summary="Get document by id",
    description="Fetch one document's metadata (ownership enforced).",
    operation_id="documents_get",
)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    """Get a document by id if it belongs to the current user."""
    doc = await db.get(DocumentSource, document_id)
    if doc is None or doc.user_id != current_user.id or doc.deleted_at is not None:
        raise NotFoundError("Document not found")
    return DocumentRead.model_validate(doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Soft-deletes a document owned by the current user.",
    operation_id="documents_delete",
)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    """Soft-delete a document if it belongs to the current user."""
    doc = await db.get(DocumentSource, document_id)
    if doc is None or doc.user_id != current_user.id or doc.deleted_at is not None:
        raise NotFoundError("Document not found")

    doc.deleted_at = datetime.now(timezone.utc)  # SoftDeleteMixin field
    await db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
