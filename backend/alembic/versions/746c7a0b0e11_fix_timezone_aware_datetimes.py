"""fix_timezone_aware_datetimes

Revision ID: 746c7a0b0e11
Revises: 4ef244758f3e
Create Date: 2025-12-24 20:31:01.309572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '746c7a0b0e11'
down_revision: Union[str, Sequence[str], None] = '4ef244758f3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
