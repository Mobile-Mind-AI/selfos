"""Add keywords weight priority_order is_custom to life_areas

Revision ID: 013
Revises: 012
Create Date: 2025-07-05 15:50:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to life_areas table if they don't exist

    # Get current columns
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'life_areas'
    """))
    existing_columns = [row[0] for row in result]

    # Add columns only if they don't exist
    if 'keywords' not in existing_columns:
        op.add_column('life_areas', sa.Column('keywords', postgresql.JSON(), nullable=True))

    if 'weight' not in existing_columns:
        op.add_column('life_areas', sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'))

    if 'priority_order' not in existing_columns:
        op.add_column('life_areas', sa.Column('priority_order', sa.Integer(), nullable=False, server_default='0'))

    if 'is_custom' not in existing_columns:
        op.add_column('life_areas', sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    # Drop the columns
    op.drop_column('life_areas', 'is_custom')
    op.drop_column('life_areas', 'priority_order')
    op.drop_column('life_areas', 'weight')
    op.drop_column('life_areas', 'keywords')
