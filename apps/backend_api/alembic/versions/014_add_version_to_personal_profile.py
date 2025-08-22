"""add version to personal_profile

Revision ID: 014
Revises: 013
Create Date: 2025-07-05 19:20:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add version column to personal_profiles table
    op.add_column('personal_profiles', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    # Remove version column from personal_profiles table
    op.drop_column('personal_profiles', 'version')
