"""SQLAlchemy ORM models package.

Importing this package should register all models with SQLAlchemy's Declarative
Base metadata (via class definitions). This is helpful for migrations and for
any app startup that needs to ensure all models are known.
"""

from src.models.assessment import SkillAssessmentRun, SkillAssessmentSkillResult
from src.models.career_path import CareerPath, CareerPathRecommendation, CareerPathSkill, UserCareerPathSelection
from src.models.dashboard import DashboardPhaseState
from src.models.document import DocumentSource
from src.models.marketplace import MarketplaceItem, MilestoneMarketplaceItem, RoadmapMarketplaceItem
from src.models.persona import PersonaDocument, PersonaProfile
from src.models.questionnaire import QuestionnaireResponse, QuestionnaireTemplate
from src.models.skill import PersonaSkillMap, Skill, SkillEvidence
from src.models.user import User

__all__ = [
    "User",
    "PersonaProfile",
    "PersonaDocument",
    "DocumentSource",
    "Skill",
    "SkillEvidence",
    "PersonaSkillMap",
    "QuestionnaireTemplate",
    "QuestionnaireResponse",
    "SkillAssessmentRun",
    "SkillAssessmentSkillResult",
    "CareerPath",
    "CareerPathSkill",
    "CareerPathRecommendation",
    "UserCareerPathSelection",
    "RoadmapMarketplaceItem",
    "MilestoneMarketplaceItem",
    "MarketplaceItem",
    "DashboardPhaseState",
]

