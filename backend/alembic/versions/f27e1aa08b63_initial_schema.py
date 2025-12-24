"""initial schema

Revision ID: f27e1aa08b63
Revises:
Create Date: 2025-12-24 10:25:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f27e1aa08b63'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table('users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('uuid', name='uq_users_uuid')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=False)
    op.create_index('idx_users_role', 'users', ['role'], unique=False)
    op.create_index('idx_users_status', 'users', ['status'], unique=False)
    op.create_index('idx_users_uuid', 'users', ['uuid'], unique=True)

    # Datasets
    op.create_table('datasets',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('access_level', sa.String(length=50), server_default='private', nullable=False),
        sa.Column('row_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('processed_count', sa.Integer(), server_default='0', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_datasets_slug'),
        sa.UniqueConstraint('uuid', name='uq_datasets_uuid')
    )
    op.create_index('idx_datasets_access', 'datasets', ['access_level'], unique=False)
    op.create_index('idx_datasets_slug', 'datasets', ['slug'], unique=False)
    op.create_index('idx_datasets_source', 'datasets', ['source_type'], unique=False)
    op.create_index('idx_datasets_uuid', 'datasets', ['uuid'], unique=True)

    # Property Definitions
    op.create_table('property_definitions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dataset_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('wikidata_property', sa.String(length=50), nullable=True),
        sa.Column('required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_facet', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_id', 'name', name='uq_properties_dataset_name'),
        sa.UniqueConstraint('uuid', name='uq_property_definitions_uuid')
    )
    op.create_index('idx_properties_dataset', 'property_definitions', ['dataset_id'], unique=False)
    op.create_index('idx_properties_uuid', 'property_definitions', ['uuid'], unique=True)

    # Dataset Entries
    op.create_table('dataset_entries',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dataset_id', sa.BigInteger(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('external_url', sa.String(length=500), nullable=True),
        sa.Column('display_name', sa.String(length=500), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_id', 'external_id', name='uq_dataset_entries_external'),
        sa.UniqueConstraint('uuid', name='uq_dataset_entries_uuid')
    )
    op.create_index('idx_dataset_entries_dataset', 'dataset_entries', ['dataset_id'], unique=False)
    op.create_index('idx_dataset_entries_display_name', 'dataset_entries', ['display_name'], unique=False)
    op.create_index('idx_dataset_entries_external_id', 'dataset_entries', ['dataset_id', 'external_id'], unique=False)
    op.create_index('idx_dataset_entries_uuid', 'dataset_entries', ['uuid'], unique=True)

    # Dataset Entry Properties (EAV)
    op.create_table('dataset_entry_properties',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dataset_entry_id', sa.BigInteger(), nullable=False),
        sa.Column('property_id', sa.BigInteger(), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('value_normalized', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('ordinal', sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_entry_id'], ['dataset_entries.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['property_definitions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_entry_id', 'property_id', 'ordinal', name='uq_dep_entry_property_ordinal'),
        sa.UniqueConstraint('uuid', name='uq_dataset_entry_properties_uuid')
    )
    op.create_index('idx_dep_entry', 'dataset_entry_properties', ['dataset_entry_id'], unique=False)
    op.create_index('idx_dep_entry_property', 'dataset_entry_properties', ['dataset_entry_id', 'property_id'], unique=False)
    op.create_index('idx_dep_property', 'dataset_entry_properties', ['property_id'], unique=False)
    op.create_index('idx_dep_uuid', 'dataset_entry_properties', ['uuid'], unique=True)
    op.create_index('idx_dep_value_normalized', 'dataset_entry_properties', ['value_normalized'], unique=False)

    # Projects
    op.create_table('projects',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dataset_id', sa.BigInteger(), nullable=False),
        sa.Column('owner_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('stats', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='uq_projects_uuid')
    )
    op.create_index('idx_projects_dataset', 'projects', ['dataset_id'], unique=False)
    op.create_index('idx_projects_owner', 'projects', ['owner_id'], unique=False)
    op.create_index('idx_projects_status', 'projects', ['status'], unique=False)
    op.create_index('idx_projects_uuid', 'projects', ['uuid'], unique=True)

    # Match Candidates
    # Forward declaration needed because Tasks reference MatchCandidates
    # We'll create the table first, then Tasks, then add FKs
    op.create_table('match_candidates',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('wikidata_id', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('score', sa.SmallInteger(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('score_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('matched_properties', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by_id', sa.BigInteger(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ),
        # task_id FK added after Tasks table creation
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='uq_match_candidates_uuid')
    )
    op.create_index('idx_mc_score', 'match_candidates', ['score'], unique=False)
    op.create_index('idx_mc_source', 'match_candidates', ['source'], unique=False)
    op.create_index('idx_mc_status', 'match_candidates', ['status'], unique=False)
    op.create_index('idx_mc_task', 'match_candidates', ['task_id'], unique=False)
    op.create_index('idx_mc_task_status', 'match_candidates', ['task_id', 'status'], unique=False)
    op.create_index('idx_mc_uuid', 'match_candidates', ['uuid'], unique=True)
    op.create_index('idx_mc_wikidata', 'match_candidates', ['wikidata_id'], unique=False)
    op.create_index('idx_mc_reviewed_by', 'match_candidates', ['reviewed_by_id'], unique=False)

    # Tasks
    op.create_table('tasks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('dataset_entry_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('accepted_candidate_id', sa.BigInteger(), nullable=True),
        sa.Column('accepted_wikidata_id', sa.String(length=20), nullable=True),
        sa.Column('candidate_count', sa.Integer(), nullable=False),
        sa.Column('highest_score', sa.SmallInteger(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by_id', sa.BigInteger(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['accepted_candidate_id'], ['match_candidates.id'], use_alter=True, name='fk_tasks_accepted_candidate'),
        sa.ForeignKeyConstraint(['dataset_entry_id'], ['dataset_entries.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'dataset_entry_id', name='uq_tasks_project_entry'),
        sa.UniqueConstraint('uuid', name='uq_tasks_uuid')
    )
    op.create_index('idx_tasks_accepted_wikidata', 'tasks', ['accepted_wikidata_id'], unique=False)
    op.create_index('idx_tasks_entry', 'tasks', ['dataset_entry_id'], unique=False)
    op.create_index('idx_tasks_highest_score', 'tasks', ['highest_score'], unique=False)
    op.create_index('idx_tasks_project', 'tasks', ['project_id'], unique=False)
    op.create_index('idx_tasks_project_status', 'tasks', ['project_id', 'status'], unique=False)
    op.create_index('idx_tasks_reviewed_by', 'tasks', ['reviewed_by_id'], unique=False)
    op.create_index('idx_tasks_status', 'tasks', ['status'], unique=False)
    op.create_index('idx_tasks_uuid', 'tasks', ['uuid'], unique=True)

    # Add circular FK for match_candidates.task_id
    op.create_foreign_key('fk_mc_task', 'match_candidates', 'tasks', ['task_id'], ['id'])

    # Audit Logs (No soft delete, inherits from SQLModel directly)
    op.create_table('audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.BigInteger(), nullable=True),
        sa.Column('entity_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='uq_audit_logs_uuid')
    )
    op.create_index('idx_audit_action', 'audit_logs', ['action'], unique=False)
    op.create_index('idx_audit_created', 'audit_logs', ['created_at'], unique=False)
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_audit_entity_uuid', 'audit_logs', ['entity_type', 'entity_uuid'], unique=False)
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    # Drop circular FK first
    op.drop_constraint('fk_mc_task', 'match_candidates', type_='foreignkey')
    op.drop_table('tasks')
    op.drop_table('match_candidates')
    op.drop_table('projects')
    op.drop_table('dataset_entry_properties')
    op.drop_table('dataset_entries')
    op.drop_table('property_definitions')
    op.drop_table('datasets')
    op.drop_table('users')
