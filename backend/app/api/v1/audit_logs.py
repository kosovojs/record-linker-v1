"""
Audit Log API endpoints.

Read-only endpoints for viewing audit logs:
- GET /audit-logs - List logs (paginated, filtered)
- GET /audit-logs/{uuid} - Get single log
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query, Path

from app.api.deps import DbSession, Pagination
from app.api.utils import raise_not_found
from app.schemas.audit_log import AuditLogRead
from app.schemas.common import PaginatedResponse
from app.services.audit_service import AuditLogService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AuditLogRead])
async def list_audit_logs(
    db: DbSession,
    pagination: Pagination,
    entity_type: str | None = Query(
        default=None,
        description="Filter by the type of entity affected (e.g., project, dataset)",
        examples=["project"],
    ),
    entity_uuid: UUID | None = Query(
        default=None,
        description="Filter by the unique identifier of the affected entity",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
    action: str | None = Query(
        default=None,
        description="Filter by the action performed (e.g., create, update, delete)",
        examples=["update"],
    ),
    from_date: datetime | None = Query(
        default=None,
        description="Filter logs from this date (ISO 8601)",
        examples=["2023-01-01T00:00:00"],
    ),
    to_date: datetime | None = Query(
        default=None,
        description="Filter logs up to this date (ISO 8601)",
        examples=["2023-12-31T23:59:59"],
    ),
):
    """List all audit logs with pagination and optional filters."""
    service = AuditLogService(db)
    items, total = await service.get_list(
        pagination=pagination,
        entity_type=entity_type,
        entity_uuid=entity_uuid,
        action=action,
        from_date=from_date,
        to_date=to_date,
    )

    return PaginatedResponse[AuditLogRead](
        items=[AuditLogRead.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_more=(pagination.page * pagination.page_size) < total,
    )


@router.get("/{uuid}", response_model=AuditLogRead)
async def get_audit_log(
    db: DbSession,
    uuid: UUID = Path(
        ...,
        description="The unique identifier of the audit log entry",
        examples=["330e8400-e29b-41d4-a716-446655440000"],
    ),
):
    """Get a single audit log by UUID."""
    service = AuditLogService(db)
    log = await service.get_by_uuid(uuid)

    if not log:
        raise_not_found("Audit log")

    return AuditLogRead.model_validate(log)
