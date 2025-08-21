"""Add preferences and custom_answers to personal_profiles

Revision ID: 009
Revises: 008
Create Date: 2025-07-03 13:58:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add preferences and custom_answers columns to personal_profiles table."""
    
    # Add preferences column (JSON)
    op.add_column('personal_profiles',
                  sa.Column('preferences', postgresql.JSONB(), nullable=True))
    
    # Add custom_answers column (JSON)
    op.add_column('personal_profiles',
                  sa.Column('custom_answers', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    """Remove preferences and custom_answers columns from personal_profiles table."""
    
    # Remove added columns
    op.drop_column('personal_profiles', 'custom_answers')
    op.drop_column('personal_profiles', 'preferences')