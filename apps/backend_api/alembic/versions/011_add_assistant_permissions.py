"""Add assistant permissions system

Revision ID: 011
Revises: 010
Create Date: 2025-07-04 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None

def upgrade():
    # No enum needed - permission_level is just a String column
    print("🔄 Adding assistant permissions system...")

    # Check if assistant_permissions table already exists
    from alembic import context
    connection = context.get_bind()

    # Check if table exists
    result = connection.execute(sa.text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'assistant_permissions'
        AND table_schema = current_schema()
    """))

    if not result.fetchone():
        # Add columns to assistant_profiles if they don't exist
        # Check for version column
        version_result = connection.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'assistant_profiles' 
            AND column_name = 'version'
            AND table_schema = current_schema()
        """))
        if not version_result.fetchone():
            op.add_column('assistant_profiles', sa.Column('version', sa.BigInteger(), nullable=False, server_default='0'))

        # Check for owner_id column
        owner_result = connection.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'assistant_profiles' 
            AND column_name = 'owner_id'
            AND table_schema = current_schema()
        """))
        if not owner_result.fetchone():
            op.add_column('assistant_profiles', sa.Column('owner_id', sa.String(), nullable=True))
            # Update existing assistant_profiles to set owner_id from user_id
            op.execute("UPDATE assistant_profiles SET owner_id = user_id WHERE owner_id IS NULL")
            op.alter_column('assistant_profiles', 'owner_id', nullable=False)

        # Check for is_public column
        public_result = connection.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'assistant_profiles' 
            AND column_name = 'is_public'
            AND table_schema = current_schema()
        """))
        if not public_result.fetchone():
            op.add_column('assistant_profiles', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))

        # Create assistant_permissions table
        op.create_table('assistant_permissions',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('assistant_id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('permission_level', sa.String(), nullable=False),
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

    # No enum to drop since we use String columns
