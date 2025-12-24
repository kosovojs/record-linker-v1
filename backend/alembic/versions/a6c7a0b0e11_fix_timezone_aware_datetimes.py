"""fix timezone aware datetimes

Revision ID: a6c7a0b0e11
Revises: 4ef244758f3e
Create Date: 2024-12-24 20:29:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6c7a0b0e11'
down_revision: Union[str, None] = '4ef244758f3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables and their datetime columns
    schema_map = {
        'users': ['created_at', 'updated_at', 'deleted_at', 'last_login_at'],
        'datasets': ['created_at', 'updated_at', 'deleted_at', 'last_synced_at'],
        'property_definitions': ['created_at', 'updated_at', 'deleted_at'],
        'dataset_entries': ['created_at', 'updated_at', 'deleted_at'],
        'dataset_entry_properties': ['created_at', 'updated_at', 'deleted_at'],
        'projects': ['created_at', 'updated_at', 'deleted_at', 'started_at', 'completed_at'],
        'tasks': ['created_at', 'updated_at', 'deleted_at', 'processing_started_at', 'processing_completed_at', 'reviewed_at'],
        'match_candidates': ['created_at', 'updated_at', 'deleted_at', 'reviewed_at'],
        'audit_logs': ['created_at']
    }

    for table, columns in schema_map.items():
        for column in columns:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=True),
                postgresql_using=f"{column}::timestamp with time zone"
            )


def downgrade() -> None:
    # Reverting to naive timestamps
    schema_map = {
        'users': ['created_at', 'updated_at', 'deleted_at', 'last_login_at'],
        'datasets': ['created_at', 'updated_at', 'deleted_at', 'last_synced_at'],
        'property_definitions': ['created_at', 'updated_at', 'deleted_at'],
        'dataset_entries': ['created_at', 'updated_at', 'deleted_at'],
        'dataset_entry_properties': ['created_at', 'updated_at', 'deleted_at'],
        'projects': ['created_at', 'updated_at', 'deleted_at', 'started_at', 'completed_at'],
        'tasks': ['created_at', 'updated_at', 'deleted_at', 'processing_started_at', 'processing_completed_at', 'reviewed_at'],
        'match_candidates': ['created_at', 'updated_at', 'deleted_at', 'reviewed_at'],
        'audit_logs': ['created_at']
    }

    for table, columns in schema_map.items():
        for column in columns:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=False),
                postgresql_using=f"{column}::timestamp without time zone"
            )
