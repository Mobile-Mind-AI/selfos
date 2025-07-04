"""Add version field to Project, Task, LifeArea and MediaAttachment models for sync support

Revision ID: 012_add_version_to_sync_models
Revises: 011_assistant_permissions
Create Date: 2025-07-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012_add_version_to_sync_models'
down_revision = '011_assistant_permissions'
branch_labels = None
depends_on = None


def upgrade():
    # Add version field to projects table
    op.add_column('projects', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # Add version field to tasks table
    op.add_column('tasks', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # Add version field to life_areas table
    op.add_column('life_areas', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('life_areas', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Add version field to media_attachments table
    op.add_column('media_attachments', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    # Update existing records to have updated_at if null
    op.execute("UPDATE life_areas SET updated_at = created_at WHERE updated_at IS NULL")


def downgrade():
    # Remove version fields
    op.drop_column('media_attachments', 'version')
    op.drop_column('life_areas', 'updated_at')
    op.drop_column('life_areas', 'version')
    op.drop_column('tasks', 'version')
    op.drop_column('projects', 'version')