from __future__ import annotations

from fastapi import APIRouter

from src.api.routes.v1.assessments import router as assessments_router
from src.api.routes.v1.auth import router as auth_router
from src.api.routes.v1.career_paths import router as career_paths_router
from src.api.routes.v1.dashboard import router as dashboard_router
from src.api.routes.v1.documents import router as documents_router
from src.api.routes.v1.marketplace import router as marketplace_router
from src.api.routes.v1.personas import router as personas_router
from src.api.routes.v1.questionnaires import router as questionnaires_router
from src.api.routes.v1.roadmaps import router as roadmaps_router
from src.api.routes.v1.skills import router as skills_router
from src.api.routes.v1.users import router as users_router

router = APIRouter()

# Existing sample CRUD endpoints
router.include_router(users_router, prefix="/users", tags=["Users"])

# Endpoint catalog domains
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(documents_router, prefix="/documents", tags=["Documents"])
router.include_router(personas_router, prefix="/personas", tags=["Personas"])

# Skills taxonomy + evidence.
# NOTE: catalog includes POST /skills/{skill_id}/evidence and also GET /skill-evidence.
# We expose GET /skills/evidence for a cohesive router; add an alias route later if strict parity is required.
router.include_router(skills_router, prefix="/skills", tags=["Skills"])

# NOTE: catalog includes POST /questionnaire-responses (top-level).
# We expose POST /questionnaires/responses for cohesive grouping; add an alias route later if strict parity is required.
router.include_router(questionnaires_router, prefix="/questionnaires", tags=["Questionnaires"])

router.include_router(assessments_router, prefix="/assessments", tags=["Assessments"])

# NOTE: catalog paths use /career-paths and /career-path-recommendations and /career-path-selections.
# We expose recommendations + selections as subpaths under /career-paths for routing coherence:
# - GET /career-paths/recommendations
# - POST /career-paths/selections
router.include_router(career_paths_router, prefix="/career-paths", tags=["CareerPaths"])

router.include_router(roadmaps_router, prefix="/roadmaps", tags=["Roadmaps"])
router.include_router(marketplace_router, prefix="/marketplace", tags=["Marketplace"])
