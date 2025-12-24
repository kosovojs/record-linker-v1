"""
Audit Log service for read-only operations and logging.

Audit logs are:
- Immutable (no update/delete)
- Created by service layer during actions
- Queryable by entity_type, action, date range
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate
from app.schemas.common import PaginationParams


class AuditLogService:
    """Service for AuditLog read operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_uuid(self, uuid: UUID) -> AuditLog | None:
        """Get an audit log by UUID."""
        stmt = select(AuditLog).where(AuditLog.uuid == uuid)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        pagination: PaginationParams,
        entity_type: str | None = None,
        entity_uuid: UUID | None = None,
        action: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        """Get paginated list of audit logs with filters."""
        base_query = select(AuditLog)

        # Apply filters
        if entity_type:
            base_query = base_query.where(AuditLog.entity_type == entity_type)
        if entity_uuid:
            base_query = base_query.where(AuditLog.entity_uuid == entity_uuid)
        if action:
            base_query = base_query.where(AuditLog.action == action)
        if from_date:
            base_query = base_query.where(AuditLog.created_at >= from_date)
        if to_date:
            base_query = base_query.where(AuditLog.created_at <= to_date)

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        paginated_query = (
            base_query
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(paginated_query)
        items = list(result.scalars().all())

        return items, total

    async def log_action(
        self,
        action: str,
        entity_type: str,
        entity_uuid: UUID | None = None,
        entity_id: int | None = None,
        user_id: int | None = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        description: str | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_uuid=entity_uuid,
            entity_id=entity_id,
            user_id=user_id,
            old_value=old_value,
            new_value=new_value,
            context=context or {},
            description=description,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log


def get_audit_log_service(db: AsyncSession) -> AuditLogService:
    """Factory function for AuditLogService."""
    return AuditLogService(db)
