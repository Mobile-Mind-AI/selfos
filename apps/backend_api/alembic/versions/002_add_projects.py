"""Add projects

Revision ID: 002
Revises: 001
Create Date: 2025-07-01 03:46:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projects table
    op.create_table('projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('life_area_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(), nullable=False, server_default='todo'),
    sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('target_date', sa.DateTime(), nullable=True),
    sa.Column('priority', sa.String(), nullable=False, server_default='medium'),
    sa.Column('phases', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['life_area_id'], ['life_areas.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index('ix_projects_user_created', 'projects', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_projects_user_status', 'projects', ['user_id', 'status'], unique=False)
    op.create_index('ix_projects_life_area_created', 'projects', ['life_area_id', sa.text('created_at DESC')], unique=False)
    op.create_index('ix_projects_user_priority', 'projects', ['user_id', 'priority'], unique=False)
    
    # Add project_id to goals table
    op.add_column('goals', sa.Column('project_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_goals_project', 'goals', 'projects', ['project_id'], ['id'])
    op.create_index('ix_goals_project_created', 'goals', ['project_id', sa.text('created_at DESC')], unique=False)
    
    # Modify tasks table to make goal_id nullable and add project_id
    op.alter_column('tasks', 'goal_id', nullable=True)
    op.add_column('tasks', sa.Column('project_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_tasks_project', 'tasks', 'projects', ['project_id'], ['id'])
    op.create_index('ix_tasks_project_created', 'tasks', ['project_id', sa.text('created_at DESC')], unique=False)
    
    # Add project_id to media_attachments table
    op.add_column('media_attachments', sa.Column('project_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_media_project', 'media_attachments', 'projects', ['project_id'], ['id'])
    op.create_index('ix_media_project', 'media_attachments', ['project_id', sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    # Remove project_id from media_attachments
    op.drop_index('ix_media_project', table_name='media_attachments')
    op.drop_constraint('fk_media_project', 'media_attachments', type_='foreignkey')
    op.drop_column('media_attachments', 'project_id')
    
    # Remove project_id from tasks and revert goal_id to not nullable
    op.drop_index('ix_tasks_project_created', table_name='tasks')
    op.drop_constraint('fk_tasks_project', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'project_id')
    op.alter_column('tasks', 'goal_id', nullable=False)
    
    # Remove project_id from goals
    op.drop_index('ix_goals_project_created', table_name='goals')
    op.drop_constraint('fk_goals_project', 'goals', type_='foreignkey')
    op.drop_column('goals', 'project_id')
    
    # Drop projects table
    op.drop_table('projects')