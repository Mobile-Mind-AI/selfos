"""Add assistant permissions system

Revision ID: 011
Revises: 010
Create Date: 2025-07-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None

def upgrade():
    # Create permission enum type
    permission_type = postgresql.ENUM('read', 'edit', 'admin', 'owner', name='permission_type')
    permission_type.create(op.get_bind())
    
    # Add version column to assistant_profiles
    op.add_column('assistant_profiles', sa.Column('version', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('assistant_profiles', sa.Column('owner_id', sa.String(), nullable=True))
    op.add_column('assistant_profiles', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))
    
    # Update existing assistant_profiles to set owner_id from user_id
    op.execute("UPDATE assistant_profiles SET owner_id = user_id WHERE owner_id IS NULL")
    op.alter_column('assistant_profiles', 'owner_id', nullable=False)
    
    # Create assistant_permissions table
    op.create_table('assistant_permissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('assistant_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('permission_level', permission_type, nullable=False),
        sa.Column('granted_by', sa.String(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['assistant_id'], ['assistant_profiles.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('assistant_id', 'user_id', name='uq_assistant_user_permission')
    )
    
    # Create indexes
    op.create_index('ix_assistant_permissions_user', 'assistant_permissions', ['user_id'])
    op.create_index('ix_assistant_permissions_assistant', 'assistant_permissions', ['assistant_id'])
    op.create_index('ix_assistant_profiles_owner', 'assistant_profiles', ['owner_id'])

def downgrade():
    # Drop indexes
    op.drop_index('ix_assistant_profiles_owner', table_name='assistant_profiles')
    op.drop_index('ix_assistant_permissions_assistant', table_name='assistant_permissions')
    op.drop_index('ix_assistant_permissions_user', table_name='assistant_permissions')
    
    # Drop table
    op.drop_table('assistant_permissions')
    
    # Remove columns
    op.drop_column('assistant_profiles', 'is_public')
    op.drop_column('assistant_profiles', 'owner_id')
    op.drop_column('assistant_profiles', 'version')
    
    # Drop enum type
    permission_type = postgresql.ENUM('read', 'edit', 'admin', 'owner', name='permission_type')
    permission_type.drop(op.get_bind())