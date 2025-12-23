"""
Project model - top-level reconciliation work unit.

Design notes:
- One project = one dataset
- Denormalized task counts avoid expensive aggregation queries
- config JSONB stores matching parameters
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship

from app.models.base import BaseTableModel

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.task import Task
    from app.models.user import User

__all__ = ["Project"]


class Project(BaseTableModel, table=True):
    """
    A reconciliation project for matching dataset entries to Wikidata.
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
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Status
    status: str = Field(
        default="draft",
        sa_column=Column(String(50), nullable=False),
    )

    # Denormalized counts
    task_count: int = Field(default=0)
    tasks_completed: int = Field(default=0)
    tasks_with_candidates: int = Field(default=0)

    # Project configuration
    config: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    # Timing
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    dataset: "Dataset" = Relationship(back_populates="projects")
    owner: "User" = Relationship(back_populates="projects")
    tasks: list["Task"] = Relationship(back_populates="project")
