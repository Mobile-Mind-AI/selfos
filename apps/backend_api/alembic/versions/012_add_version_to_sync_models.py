"""Add version field to Project, Task, LifeArea and MediaAttachment models for sync support

Revision ID: 012
Revises: 011
Create Date: 2025-07-04 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade():
    from alembic import context

    connection = context.get_bind()

    # Check and add version field to projects table
    result = connection.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'version' AND table_schema = current_schema()
    """
        )
    )
    if not result.fetchone():
        op.add_column(
            "projects",
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        )

    # Check and add version field to tasks table
    result = connection.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'version' AND table_schema = current_schema()
    """
        )
    )
    if not result.fetchone():
        op.add_column(
            "tasks",
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        )

    # Check and add version field to life_areas table
    result = connection.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'life_areas' AND column_name = 'version' AND table_schema = current_schema()
    """
        )
    )
    if not result.fetchone():
        op.add_column(
            "life_areas",
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        )

    # Check and add updated_at field to life_areas table
    result = connection.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'life_areas' AND column_name = 'updated_at' AND table_schema = current_schema()
    """
        )
    )
    if not result.fetchone():
        op.add_column(
            "life_areas", sa.Column("updated_at", sa.DateTime(), nullable=True)
        )
        # Update existing records to have updated_at if null
        op.execute(
            "UPDATE life_areas SET updated_at = created_at WHERE updated_at IS NULL"
        )

    # Check and add version field to media_attachments table
    result = connection.execute(
        sa.text(
            """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'media_attachments' AND column_name = 'version' AND table_schema = current_schema()
    """
        )
    )
    if not result.fetchone():
        op.add_column(
            "media_attachments",
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        )


def downgrade():
    # Remove version fields
    op.drop_column("media_attachments", "version")
    op.drop_column("life_areas", "updated_at")
    op.drop_column("life_areas", "version")
    op.drop_column("tasks", "version")
    op.drop_column("projects", "version")
