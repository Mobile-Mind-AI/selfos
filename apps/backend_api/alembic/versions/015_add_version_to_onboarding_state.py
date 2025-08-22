"""add_version_to_onboarding_state

Revision ID: 015
Revises: 014
Create Date: 2025-07-11 14:05:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    # Add version column to onboarding_states table
    op.add_column('onboarding_states', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))


def downgrade():
    # Remove version column from onboarding_states table
    op.drop_column('onboarding_states', 'version')