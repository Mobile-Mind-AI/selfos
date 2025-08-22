"""Add entity knowledge graph tables

Revision ID: 001_add_entity_knowledge_graph
Revises:
Create Date: 2025-01-12 18:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_entity_knowledge_graph'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create entity_types table
    op.create_table('entity_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_entity_type_name')
    )
    op.create_index(op.f('ix_entity_types_id'), 'entity_types', ['id'], unique=False)
    op.create_index('ix_entity_types_is_system', 'entity_types', ['is_system'], unique=False)
    op.create_index('ix_entity_types_user_name', 'entity_types', ['user_id', 'name'], unique=False)

    # Create entities table
    op.create_table('entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('entity_type_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('external_source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entity_type_id'], ['entity_types.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entities_id'), 'entities', ['id'], unique=False)
    op.create_index('ix_entities_external', 'entities', ['external_source', 'external_id'], unique=False)
    op.create_index('ix_entities_user_created', 'entities', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_entities_user_name', 'entities', ['user_id', 'name'], unique=False)
    op.create_index('ix_entities_user_type', 'entities', ['user_id', 'entity_type_id'], unique=False)

    # Create entity_relationships table
    op.create_table('entity_relationships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('source_entity_id', sa.Integer(), nullable=False),
        sa.Column('target_entity_id', sa.Integer(), nullable=False),
        sa.Column('relationship_type', sa.String(length=100), nullable=False),
        sa.Column('properties', sa.JSON(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.uid'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'source_entity_id', 'target_entity_id', 'relationship_type', name='uq_entity_relationship')
    )
    op.create_index(op.f('ix_entity_relationships_id'), 'entity_relationships', ['id'], unique=False)
    op.create_index('ix_entity_relationships_source', 'entity_relationships', ['source_entity_id'], unique=False)
    op.create_index('ix_entity_relationships_target', 'entity_relationships', ['target_entity_id'], unique=False)
    op.create_index('ix_entity_relationships_type', 'entity_relationships', ['relationship_type'], unique=False)
    op.create_index('ix_entity_relationships_user', 'entity_relationships', ['user_id'], unique=False)

    # Create association tables for many-to-many relationships
    op.create_table('goal_entities',
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('goal_id', 'entity_id')
    )
    op.create_index('ix_goal_entities_entity', 'goal_entities', ['entity_id'], unique=False)
    op.create_index('ix_goal_entities_goal', 'goal_entities', ['goal_id'], unique=False)

    op.create_table('project_entities',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id', 'entity_id')
    )
    op.create_index('ix_project_entities_entity', 'project_entities', ['entity_id'], unique=False)
    op.create_index('ix_project_entities_project', 'project_entities', ['project_id'], unique=False)

    op.create_table('task_entities',
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('task_id', 'entity_id')
    )
    op.create_index('ix_task_entities_entity', 'task_entities', ['entity_id'], unique=False)
    op.create_index('ix_task_entities_task', 'task_entities', ['task_id'], unique=False)

    # Insert some default entity types
    op.execute("""
        INSERT INTO entity_types (user_id, name, description, icon, color, is_system, created_at, updated_at)
        VALUES
        ('SYSTEM', 'Person', 'An individual person', 'person', '#4A90E2', true, NOW(), NOW()),
        ('SYSTEM', 'Organization', 'A company, institution, or group', 'business', '#50E3C2', true, NOW(), NOW()),
        ('SYSTEM', 'Place', 'A physical or virtual location', 'place', '#F5A623', true, NOW(), NOW()),
        ('SYSTEM', 'Event', 'An occurrence or happening', 'event', '#BD10E0', true, NOW(), NOW()),
        ('SYSTEM', 'Concept', 'An abstract idea or principle', 'lightbulb', '#7ED321', true, NOW(), NOW())
    """)


def downgrade() -> None:
    # Drop association tables
    op.drop_index('ix_task_entities_task', table_name='task_entities')
    op.drop_index('ix_task_entities_entity', table_name='task_entities')
    op.drop_table('task_entities')

    op.drop_index('ix_project_entities_project', table_name='project_entities')
    op.drop_index('ix_project_entities_entity', table_name='project_entities')
    op.drop_table('project_entities')

    op.drop_index('ix_goal_entities_goal', table_name='goal_entities')
    op.drop_index('ix_goal_entities_entity', table_name='goal_entities')
    op.drop_table('goal_entities')

    # Drop entity_relationships table
    op.drop_index('ix_entity_relationships_user', table_name='entity_relationships')
    op.drop_index('ix_entity_relationships_type', table_name='entity_relationships')
    op.drop_index('ix_entity_relationships_target', table_name='entity_relationships')
    op.drop_index('ix_entity_relationships_source', table_name='entity_relationships')
    op.drop_index(op.f('ix_entity_relationships_id'), table_name='entity_relationships')
    op.drop_table('entity_relationships')

    # Drop entities table
    op.drop_index('ix_entities_user_type', table_name='entities')
    op.drop_index('ix_entities_user_name', table_name='entities')
    op.drop_index('ix_entities_user_created', table_name='entities')
    op.drop_index('ix_entities_external', table_name='entities')
    op.drop_index(op.f('ix_entities_id'), table_name='entities')
    op.drop_table('entities')

    # Drop entity_types table
    op.drop_index('ix_entity_types_user_name', table_name='entity_types')
    op.drop_index('ix_entity_types_is_system', table_name='entity_types')
    op.drop_index(op.f('ix_entity_types_id'), table_name='entity_types')
    op.drop_table('entity_types')
