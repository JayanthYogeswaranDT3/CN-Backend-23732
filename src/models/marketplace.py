from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.base_mixins import MarketplaceItemType, TimestampAuditMixin, UUIDPrimaryKeyMixin


class MarketplaceItem(Base, UUIDPrimaryKeyMixin, TimestampAuditMixin):
    """Marketplace catalog item (curated, platform-level).

    Matches `marketplace_items` in the Postgres MVP schema.
    """

    __tablename__ = "marketplace_items"

    title: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[MarketplaceItemType] = mapped_column(Text, nullable=False, index=True)

    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    roadmap_links = relationship("RoadmapMarketplaceItem", back_populates="marketplace_item", cascade="all, delete-orphan")
    milestone_links = relationship("MilestoneMarketplaceItem", back_populates="marketplace_item", cascade="all, delete-orphan")


Index("ix_marketplace_items_item_type", MarketplaceItem.item_type)
Index("ix_marketplace_items_is_active", MarketplaceItem.is_active)


class RoadmapMarketplaceItem(Base):
    """Junction linking marketplace items to a roadmap.

    Matches `roadmap_marketplace_item` in the Postgres MVP schema.
    Composite primary key: (roadmap_id, marketplace_item_id)
    """

    __tablename__ = "roadmap_marketplace_item"

    roadmap_id: Mapped[str] = mapped_column(ForeignKey("roadmaps.id", ondelete="CASCADE"), primary_key=True)
    marketplace_item_id: Mapped[str] = mapped_column(
        ForeignKey("marketplace_items.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    relevance_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    roadmap = relationship("Roadmap", back_populates="marketplace_links")
    marketplace_item = relationship("MarketplaceItem", back_populates="roadmap_links")


Index("ix_roadmap_marketplace_item_item_id", RoadmapMarketplaceItem.marketplace_item_id)


class MilestoneMarketplaceItem(Base):
    """Junction linking marketplace items to a milestone.

    Matches `milestone_marketplace_item` in the Postgres MVP schema.
    Composite primary key: (milestone_id, marketplace_item_id)
    """

    __tablename__ = "milestone_marketplace_item"

    milestone_id: Mapped[str] = mapped_column(ForeignKey("milestones.id", ondelete="CASCADE"), primary_key=True)
    marketplace_item_id: Mapped[str] = mapped_column(
        ForeignKey("marketplace_items.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    relevance_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    milestone = relationship("Milestone", back_populates="marketplace_links")
    marketplace_item = relationship("MarketplaceItem", back_populates="milestone_links")


Index("ix_milestone_marketplace_item_item_id", MilestoneMarketplaceItem.marketplace_item_id)

