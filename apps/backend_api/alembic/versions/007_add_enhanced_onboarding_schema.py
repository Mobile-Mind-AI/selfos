"""Add enhanced onboarding schema

Revision ID: 007
Revises: 005
Create Date: 2025-07-03 09:33:10.327070

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enhanced onboarding tables and columns."""

    # 1. Add new columns to existing onboarding_states table
    op.add_column('onboarding_states',
                  sa.Column('personal_story', postgresql.JSONB(), nullable=True))
    op.add_column('onboarding_states',
                  sa.Column('preference_learning', postgresql.JSONB(), nullable=True))
    op.add_column('onboarding_states',
                  sa.Column('context_config', postgresql.JSONB(), nullable=True))
    op.add_column('onboarding_states',
                  sa.Column('flow_version', sa.String(10), nullable=False, server_default='v1'))

    # 2. Create personal_profiles table
    op.create_table(
        'personal_profiles',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False, unique=True),
        sa.Column('current_situation', sa.Text(), nullable=True),
        sa.Column('interests', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('challenges', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('aspirations', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('motivation', sa.Text(), nullable=True),
        sa.Column('work_style', sa.String(50), nullable=True),
        sa.Column('communication_frequency', sa.String(50), nullable=True),
        sa.Column('goal_approach', sa.String(50), nullable=True),
        sa.Column('motivation_style', sa.String(50), nullable=True),
        sa.Column('story_analysis', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', name='uq_personal_profiles_user_id')
    )

    # Add index for user lookup
    op.create_index('ix_personal_profiles_user_id', 'personal_profiles', ['user_id'])

    # 3. Create custom_life_areas table
    op.create_table(
        'custom_life_areas',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('icon', sa.String(50), nullable=False, server_default='category'),
        sa.Column('color', sa.String(7), nullable=False, server_default='#6366f1'),  # Indigo default
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('priority_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ondelete='CASCADE'),
    )

    # Add indexes for custom life areas
    op.create_index('ix_custom_life_areas_user_id', 'custom_life_areas', ['user_id'])
    op.create_index('ix_custom_life_areas_priority', 'custom_life_areas', ['user_id', 'priority_order'])

    # 4. Create onboarding_analytics table for tracking
    op.create_table(
        'onboarding_analytics',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),  # 'step_start', 'step_complete', 'abandon'
        sa.Column('step_name', sa.String(50), nullable=True),  # 'welcome', 'ai_config', 'personal_config'
        sa.Column('step_number', sa.Integer(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('completion_percentage', sa.Float(), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ondelete='CASCADE'),
    )

    # Add indexes for analytics
    op.create_index('ix_onboarding_analytics_user_id', 'onboarding_analytics', ['user_id'])
    op.create_index('ix_onboarding_analytics_event', 'onboarding_analytics', ['event_type', 'created_at'])

    # 5. Update existing data to use new flow version
    # Mark existing onboarding states as v1 (legacy)
    op.execute("UPDATE onboarding_states SET flow_version = 'v1' WHERE flow_version IS NULL")

    # 6. Add default custom life areas for existing users who completed onboarding
    # This ensures backward compatibility - but check if users already have life_areas
    default_life_areas = [
        ('Health & Wellness', 'fitness_center', '#ef4444'),
        ('Work & Career', 'work', '#3b82f6'),
        ('Relationships', 'people', '#ec4899'),
        ('Personal Growth', 'psychology', '#8b5cf6'),
        ('Finances', 'account_balance', '#10b981'),
    ]

    # Only insert for users who completed onboarding but don't have custom life areas yet
    for name, icon, color in default_life_areas:
        op.execute(f"""
            INSERT INTO custom_life_areas (user_id, name, icon, color, is_custom, priority_order, created_at, updated_at)
            SELECT 
                os.user_id, 
                '{name}', 
                '{icon}', 
                '{color}', 
                false,
                (SELECT COUNT(*) FROM custom_life_areas cla2 WHERE cla2.user_id = os.user_id) + 1,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            FROM onboarding_states os 
            WHERE os.onboarding_completed = true
            AND NOT EXISTS (
                SELECT 1 FROM custom_life_areas cla 
                WHERE cla.user_id = os.user_id AND cla.name = '{name}'
            )
        """)


def downgrade() -> None:
    """Rollback enhanced onboarding changes."""

    # 1. Drop new tables
    op.drop_table('onboarding_analytics')
    op.drop_table('custom_life_areas')
    op.drop_table('personal_profiles')

    # 2. Remove new columns from onboarding_states
    op.drop_column('onboarding_states', 'flow_version')
    op.drop_column('onboarding_states', 'context_config')
    op.drop_column('onboarding_states', 'preference_learning')
    op.drop_column('onboarding_states', 'personal_story')