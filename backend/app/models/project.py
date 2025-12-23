"""
Project model - top-level reconciliation work unit.

Design notes:
- One project = one dataset (no cross-dataset projects for simplicity)
- Denormalized task counts avoid expensive aggregation queries
- config JSONB stores matching parameters that vary per project
- State machine enforced at application layer, not DB level
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field

from app.models.base import BaseTableModel

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.task import Task
    from app.models.user import User

__all__ = ["Project"]


class Project(BaseTableModel, table=True):
    """
    A reconciliation project for matching dataset entries to Wikidata.

    Projects allow breaking large datasets into manageable batches
    and trying different matching configurations. One dataset can
    have multiple projects (e.g., "Hockey players 2020s", "Coaches").
    """

    __tablename__ = "projects"
    __table_args__ = (
        Index("idx_projects_dataset", "dataset_id"),
        Index("idx_projects_owner", "owner_id"),
        Index("idx_projects_status", "status"),
        Index("idx_projects_created", "created_at"),
    )

    # Foreign keys
    dataset_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("datasets.id"), nullable=False),
    )
    owner_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=False),
    )

    # Identification
    name: str = Field(
        sa_column=Column(String(255), nullable=False),
        max_length=255,
        description="Project name (e.g., 'EP Players - Batch 1')",
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Status - validated by Pydantic, not DB
    status: str = Field(
        default="draft",
        sa_column=Column(String(50), nullable=False),
    )

    # Denormalized counts - updated by triggers or application code
    # Avoids COUNT(*) on large task tables
    task_count: int = Field(
        default=0,
        description="Total tasks in project",
    )
    tasks_completed: int = Field(
        default=0,
        description="Tasks in terminal states (reviewed, skipped, etc.)",
    )
    tasks_with_candidates: int = Field(
        default=0,
        description="Tasks with at least one candidate",
    )

    # Project configuration - matching parameters
    # auto_accept_threshold: auto-accept candidates above this score
    # search_strategies: which search methods to use
    # matching_weights: property weights for scoring
    config: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Timing
    started_at: datetime | None = Field(
        default=None,
        description="When processing began",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="When all tasks were reviewed",
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(back_populates="projects")
    owner: Mapped["User"] = relationship(back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        lazy="noload",
    )
