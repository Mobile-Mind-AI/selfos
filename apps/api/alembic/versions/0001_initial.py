"""
Initial schemas and tables

Revision ID: 0001_initial
Revises: 
Create Date: 2025-09-24
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS graph")
    op.execute("CREATE SCHEMA IF NOT EXISTS memory")
    op.execute("CREATE SCHEMA IF NOT EXISTS chat")
    op.execute("CREATE SCHEMA IF NOT EXISTS agent")
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")
    op.execute("CREATE SCHEMA IF NOT EXISTS outbox")

    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("timezone", sa.String(), nullable=True),
        sa.Column("prefs", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("email", name="ux_users_email"),
        schema="core",
    )

    # Life Areas
    op.create_table(
        "life_areas",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "name", name="ux_life_areas_user_name"),
        schema="core",
    )

    op.create_table(
        "life_area_links",
        sa.Column("life_area_id", sa.String(), sa.ForeignKey("core.life_areas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_type", sa.String(), nullable=False),
        sa.Column("object_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("object_type in ('dream','goal','project','task','habit')", name="ck_lal_object_type"),
        sa.PrimaryKeyConstraint("life_area_id", "object_type", "object_id", name="pk_life_area_link"),
        schema="core",
    )
    op.create_index("ix_lal_user_object", "life_area_links", ["user_id", "object_type", "object_id"], schema="core")

    # Dreams, Projects, Goals
    op.create_table(
        "dreams",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="incubating"),
        sa.Column("horizon", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="core",
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="core",
    )

    op.create_table(
        "goals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dream_id", sa.String(), sa.ForeignKey("core.dreams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="core",
    )
    op.create_index("ix_goals_user_created", "goals", ["user_id", "created_at"], schema="core")

    # Habits & logs
    op.create_table(
        "habits",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("schedule_rrule", sa.Text(), nullable=True),
        sa.Column("cadence_target", sa.Integer(), nullable=True),
        sa.Column("period", sa.String(), nullable=True),
        sa.Column("streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_done_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="core",
    )

    op.create_table(
        "habit_logs",
        sa.Column("habit_id", sa.String(), sa.ForeignKey("core.habits.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(), primary_key=True),
        sa.Column("value", sa.Numeric(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        schema="core",
    )

    # Tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal_id", sa.String(), sa.ForeignKey("core.goals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("core.projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("habit_id", sa.String(), sa.ForeignKey("core.habits.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("rrule", sa.Text(), nullable=True),
        sa.Column("effort_minutes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="core",
    )
    op.create_index("ix_tasks_user_status", "tasks", ["user_id", "status"], schema="core")
    op.create_index("ix_tasks_user_due", "tasks", ["user_id", "due_at"], schema="core")

    # Attachments
    op.create_table(
        "attachments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ref_type", sa.String(), nullable=False),
        sa.Column("ref_id", sa.String(), nullable=False),
        sa.Column("gcs_path", sa.String(), nullable=False),
        sa.Column("mime", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="core",
    )

    # Graph
    op.create_table(
        "nodes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("aliases", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        schema="graph",
    )
    op.create_table(
        "edges",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("src_type", sa.String(), nullable=False),
        sa.Column("src_id", sa.String(), nullable=False),
        sa.Column("rel", sa.String(), nullable=False),
        sa.Column("dst_type", sa.String(), nullable=False),
        sa.Column("dst_id", sa.String(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=True),
        sa.Column("props", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema="graph",
    )
    op.create_index("ix_graph_edges_src", "edges", ["src_type", "src_id"], schema="graph")
    op.create_index("ix_graph_edges_dst", "edges", ["dst_type", "dst_id"], schema="graph")

    # Chat
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="chat",
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("conversation_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("extracted", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="chat",
    )

    # Agent
    op.create_table(
        "agents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("scopes", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="agent",
    )

    op.create_table(
        "runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("input", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="completed"),
        sa.Column("costs", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="agent",
    )

    # Audit
    op.create_table(
        "events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("ref_type", sa.String(), nullable=True),
        sa.Column("ref_id", sa.String(), nullable=True),
        sa.Column("meta", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="audit",
    )

    # Outbox
    op.create_table(
        "events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("aggregate_type", sa.String(), nullable=True),
        sa.Column("aggregate_id", sa.String(), nullable=True),
        sa.Column("payload", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        schema="outbox",
    )

    # Memory (pgvector)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS memory.memories (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding VECTOR(1536),
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_mem_user_created ON memory.memories(user_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_mem_embedding ON memory.memories USING ivfflat (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    # Drop order reversed
    op.execute("DROP INDEX IF EXISTS memory.ix_mem_embedding")
    op.execute("DROP INDEX IF EXISTS memory.ix_mem_user_created")
    op.execute("DROP TABLE IF EXISTS memory.memories")

    for schema, tables in [
        ("outbox", ["events"]),
        ("audit", ["events"]),
        ("agent", ["runs", "agents"]),
        ("chat", ["messages", "conversations"]),
        ("graph", ["edges", "nodes"]),
        ("core", [
            "attachments",
            "tasks",
            "habit_logs",
            "habits",
            "goals",
            "projects",
            "dreams",
            "life_area_links",
            "life_areas",
            "users",
        ]),
    ]:
        for table in tables:
            op.execute(f'DROP TABLE IF EXISTS {schema}.{table} CASCADE')

    for schema in ["outbox", "audit", "agent", "chat", "graph", "core"]:
        op.execute(f'DROP SCHEMA IF EXISTS {schema} CASCADE')

