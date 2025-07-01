"""Create base tables

Revision ID: 001
Revises: 
Create Date: 2025-07-01 03:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
    sa.Column('uid', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('uid'),
    sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_uid'), 'users', ['uid'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create life_areas table
    op.create_table('life_areas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=False, server_default='10'),
    sa.Column('icon', sa.String(), nullable=True),
    sa.Column('color', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_life_areas_id'), 'life_areas', ['id'], unique=False)
    op.create_index('ix_life_areas_user_created', 'life_areas', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_life_areas_user_name', 'life_areas', ['user_id', 'name'], unique=False)
    
    # Create goals table
    op.create_table('goals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('life_area_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=False, server_default='todo'),
    sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['life_area_id'], ['life_areas.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goals_id'), 'goals', ['id'], unique=False)
    op.create_index('ix_goals_user_created', 'goals', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_goals_user_status', 'goals', ['user_id', 'status'], unique=False)
    op.create_index('ix_goals_life_area_created', 'goals', ['life_area_id', sa.text('created_at DESC')], unique=False)
    
    # Create media_attachments table
    op.create_table('media_attachments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('goal_id', sa.Integer(), nullable=True),
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('file_url', sa.Text(), nullable=False),
    sa.Column('file_type', sa.String(), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_media_attachments_id'), 'media_attachments', ['id'], unique=False)
    op.create_index('ix_media_goal', 'media_attachments', ['goal_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_media_user_created', 'media_attachments', ['user_id', sa.text('created_at DESC')], unique=False)
    
    # Create tasks table
    op.create_table('tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('goal_id', sa.Integer(), nullable=False),
    sa.Column('life_area_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(), nullable=False, server_default='todo'),
    sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
    sa.Column('dependencies', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
    sa.ForeignKeyConstraint(['life_area_id'], ['life_areas.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_index('ix_tasks_user_created', 'tasks', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_tasks_user_status', 'tasks', ['user_id', 'status'], unique=False)
    op.create_index('ix_tasks_goal_created', 'tasks', ['goal_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_tasks_due_date', 'tasks', ['user_id', 'due_date'], unique=False)
    op.create_index('ix_tasks_completed', 'tasks', ['user_id', sa.text('created_at DESC')], unique=False, postgresql_where=sa.text("status = 'completed'"))
    
    # Create memory_items table
    op.create_table('memory_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('memory_type', sa.String(), nullable=False),
    sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_items_id'), 'memory_items', ['id'], unique=False)
    op.create_index('ix_memory_user_created', 'memory_items', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_memory_user_type', 'memory_items', ['user_id', 'memory_type'], unique=False)
    
    # Create user_preferences table
    op.create_table('user_preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('default_life_area_id', sa.Integer(), nullable=True),
    sa.Column('theme', sa.String(), nullable=False, server_default='light'),
    sa.Column('language', sa.String(), nullable=False, server_default='en'),
    sa.Column('timezone', sa.String(), nullable=False, server_default='UTC'),
    sa.Column('notification_settings', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('ui_preferences', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['default_life_area_id'], ['life_areas.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_preferences_id'), 'user_preferences', ['id'], unique=False)
    
    # Create feedback_logs table
    op.create_table('feedback_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=True),
    sa.Column('feedback_type', sa.String(), nullable=False),
    sa.Column('feedback_value', sa.Float(), nullable=False),
    sa.Column('context_type', sa.String(), nullable=False),
    sa.Column('context_id', sa.String(), nullable=False),
    sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_logs_id'), 'feedback_logs', ['id'], unique=False)
    op.create_index('ix_feedback_user_created', 'feedback_logs', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_feedback_session_created', 'feedback_logs', ['session_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_feedback_context', 'feedback_logs', ['context_type', 'context_id'], unique=False)
    
    # Create story_sessions table
    op.create_table('story_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('story_type', sa.String(), nullable=False),
    sa.Column('source_goals', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
    sa.Column('source_tasks', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
    sa.Column('narrative_content', sa.Text(), nullable=True),
    sa.Column('media_urls', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
    sa.Column('status', sa.String(), nullable=False, server_default='draft'),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_story_sessions_id'), 'story_sessions', ['id'], unique=False)
    op.create_index('ix_story_user_created', 'story_sessions', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_story_user_type', 'story_sessions', ['user_id', 'story_type'], unique=False)


def downgrade() -> None:
    op.drop_table('story_sessions')
    op.drop_table('feedback_logs')
    op.drop_table('user_preferences')
    op.drop_table('memory_items')
    op.drop_table('tasks')
    op.drop_table('media_attachments')
    op.drop_table('goals')
    op.drop_table('life_areas')
    op.drop_table('users')