"""Merge entity knowledge graph into main migration chain

Revision ID: 017
Revises: 016, 001_add_entity_knowledge_graph
Create Date: 2025-08-22 18:02:15.269086

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '017'
down_revision = ('016', '001_add_entity_knowledge_graph')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass