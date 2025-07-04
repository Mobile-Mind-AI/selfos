"""Merge migration heads

Revision ID: 008
Revises: 006, 007
Create Date: 2025-07-03 09:25:32.063857

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = ('006', '007')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass