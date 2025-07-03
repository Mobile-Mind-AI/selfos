"""Add AvatarImage model for custom avatar storage

Revision ID: 005
Revises: 78b46d09ae15
Create Date: 2025-07-02 17:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '78b46d09ae15'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create avatar_images table
    op.create_table('avatar_images',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('storage_type', sa.String(), nullable=False),
        sa.Column('image_data', sa.LargeBinary(), nullable=True),
        sa.Column('storage_url', sa.String(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('thumbnail_data', sa.LargeBinary(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_avatar_images_id', 'avatar_images', ['id'], unique=False)
    op.create_index('ix_avatar_images_user_created', 'avatar_images', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_avatar_images_user_active', 'avatar_images', ['user_id', 'is_active'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_avatar_images_user_active', table_name='avatar_images')
    op.drop_index('ix_avatar_images_user_created', table_name='avatar_images')
    op.drop_index('ix_avatar_images_id', table_name='avatar_images')
    
    # Drop table
    op.drop_table('avatar_images')