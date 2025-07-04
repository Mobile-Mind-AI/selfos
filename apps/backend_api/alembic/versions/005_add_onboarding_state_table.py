"""Add OnboardingState table

Revision ID: 005
Revises: 004
Create Date: 2025-07-01 14:09:54.796113

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create onboarding_states table
    op.create_table('onboarding_states',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('completed_steps', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('assistant_profile_id', sa.String(), nullable=True),
        sa.Column('selected_life_areas', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('first_goal_id', sa.Integer(), nullable=True),
        sa.Column('first_task_id', sa.Integer(), nullable=True),
        sa.Column('theme_preference', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('temp_data', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('skip_intro', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['assistant_profile_id'], ['assistant_profiles.id'], ),
        sa.ForeignKeyConstraint(['first_goal_id'], ['goals.id'], ),
        sa.ForeignKeyConstraint(['first_task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_onboarding_states_id'), 'onboarding_states', ['id'], unique=False)
    op.create_index(op.f('ix_onboarding_states_user_id'), 'onboarding_states', ['user_id'], unique=True)
    op.create_index(op.f('ix_onboarding_states_completed'), 'onboarding_states', ['onboarding_completed'], unique=False)
    op.create_index(op.f('ix_onboarding_states_last_activity'), 'onboarding_states', ['last_activity'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_onboarding_states_last_activity'), table_name='onboarding_states')
    op.drop_index(op.f('ix_onboarding_states_completed'), table_name='onboarding_states')
    op.drop_index(op.f('ix_onboarding_states_user_id'), table_name='onboarding_states')
    op.drop_index(op.f('ix_onboarding_states_id'), table_name='onboarding_states')
    
    # Drop table
    op.drop_table('onboarding_states')