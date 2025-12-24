"""sync models with schema

Revision ID: 4ef244758f3e
Revises: f27e1aa08b63
Create Date: 2024-12-24 20:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4ef244758f3e'
down_revision: Union[str, None] = 'f27e1aa08b63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Datasets ---
    # Add missing columns
    op.add_column('datasets', sa.Column('source_url', sa.String(length=500), nullable=True))
    op.add_column('datasets', sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    op.add_column('datasets', sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))

    # entry_count (renamed from row_count or added)
    # The migration has row_count and processed_count, but the model has entry_count.
    # We will rename row_count to entry_count and drop processed_count.
    op.alter_column('datasets', 'row_count', new_column_name='entry_count')
    op.drop_column('datasets', 'processed_count')

    # Drop obsolete columns
    op.drop_column('datasets', 'access_level')
    op.drop_column('datasets', 'is_deleted')

    # Adjust lengths
    op.alter_column('datasets', 'slug', type_=sa.String(length=100))
    op.alter_column('datasets', 'entity_type', type_=sa.String(length=100))

    # --- Projects ---
    # Add missing columns
    op.add_column('projects', sa.Column('task_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('projects', sa.Column('tasks_completed', sa.Integer(), server_default='0', nullable=False))
    op.add_column('projects', sa.Column('tasks_with_candidates', sa.Integer(), server_default='0', nullable=False))
    op.add_column('projects', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('projects', sa.Column('completed_at', sa.DateTime(), nullable=True))

    # Drop obsolete columns
    # In the model, 'stats' is no longer a top-level field (it was replaced by denormalized counts)
    op.drop_column('projects', 'stats')
    op.drop_column('projects', 'is_deleted')

    # Add index for created_at (present in model args)
    op.create_index('idx_projects_created', 'projects', ['created_at'], unique=False)

    # --- Other Tables: Drop is_deleted ---
    tables_to_clean = [
        'users',
        'property_definitions',
        'dataset_entries',
        'dataset_entry_properties',
        'match_candidates',
        'tasks'
    ]
    for table in tables_to_clean:
        op.drop_column(table, 'is_deleted')


def downgrade() -> None:
    # --- Other Tables ---
    tables_to_clean = [
        'users',
        'property_definitions',
        'dataset_entries',
        'dataset_entry_properties',
        'match_candidates',
        'tasks'
    ]
    for table in tables_to_clean:
        op.add_column(table, sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))

    # --- Projects ---
    op.drop_index('idx_projects_created', table_name='projects')
    op.add_column('projects', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('projects', sa.Column('stats', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.drop_column('projects', 'completed_at')
    op.drop_column('projects', 'started_at')
    op.drop_column('projects', 'tasks_with_candidates')
    op.drop_column('projects', 'tasks_completed')
    op.drop_column('projects', 'task_count')

    # --- Datasets ---
    op.alter_column('datasets', 'entity_type', type_=sa.String(length=50))
    op.alter_column('datasets', 'slug', type_=sa.String(length=255))
    op.add_column('datasets', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('datasets', sa.Column('access_level', sa.String(length=50), server_default='private', nullable=False))
    # Note: processed_count was integer, resetting to 0
    op.add_column('datasets', sa.Column('processed_count', sa.Integer(), server_default='0', nullable=False))
    op.alter_column('datasets', 'entry_count', new_column_name='row_count')
    op.drop_column('datasets', 'extra_data')
    op.drop_column('datasets', 'last_synced_at')
    op.drop_column('datasets', 'source_url')
