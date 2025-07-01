"""Add assistant profiles table

Revision ID: 004
Revises: 003
Create Date: 2025-07-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create assistant_profiles table
    op.create_table('assistant_profiles',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('ai_model', sa.String(), nullable=False, server_default='gpt-3.5-turbo'),
    sa.Column('language', sa.String(), nullable=False, server_default='en'),
    sa.Column('requires_confirmation', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('style', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{"formality": 50, "directness": 50, "humor": 30, "empathy": 70, "motivation": 60}'),
    sa.Column('dialogue_temperature', sa.Float(), nullable=False, server_default='0.8'),
    sa.Column('intent_temperature', sa.Float(), nullable=False, server_default='0.3'),
    sa.Column('custom_instructions', sa.Text(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index(op.f('ix_assistant_profiles_id'), 'assistant_profiles', ['id'], unique=False)
    op.create_index('ix_assistant_profiles_user_default', 'assistant_profiles', ['user_id', 'is_default'], unique=False)
    op.create_index('ix_assistant_profiles_user_active', 'assistant_profiles', ['user_id', 'is_active'], unique=False)
    op.create_index('ix_assistant_profiles_user_created', 'assistant_profiles', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_assistant_profiles_model_language', 'assistant_profiles', ['ai_model', 'language'], unique=False)


def downgrade() -> None:
    op.drop_table('assistant_profiles')