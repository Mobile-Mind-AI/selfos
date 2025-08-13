"""
Entity models for knowledge graph functionality.
These models allow users to create entities (people, places, organizations, etc.)
and establish relationships between them, forming a knowledge graph.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Index, Table, UniqueConstraint, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

# Association tables for many-to-many relationships between entities and other models
goal_entities = Table(
    'goal_entities',
    Base.metadata,
    Column('goal_id', Integer, ForeignKey('goals.id', ondelete='CASCADE'), primary_key=True),
    Column('entity_id', Integer, ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Index('ix_goal_entities_goal', 'goal_id'),
    Index('ix_goal_entities_entity', 'entity_id')
)

project_entities = Table(
    'project_entities',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    Column('entity_id', Integer, ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Index('ix_project_entities_project', 'project_id'),
    Index('ix_project_entities_entity', 'entity_id')
)

task_entities = Table(
    'task_entities',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('entity_id', Integer, ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Index('ix_task_entities_task', 'task_id'),
    Index('ix_task_entities_entity', 'entity_id')
)

# For compatibility with the __init__.py imports
GoalEntity = goal_entities
ProjectEntity = project_entities
TaskEntity = task_entities


class EntityType(Base):
    """
    Defines the types/categories of entities (e.g., Person, Place, Organization, etc.)
    Users can define their own entity types for customization.
    """
    __tablename__ = "entity_types"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    name = Column(String(50), nullable=False)  # e.g., "Person", "Place", "Organization"
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Optional icon identifier for UI
    color = Column(String(50), nullable=True)  # Optional color for UI visualization
    
    # System flag to distinguish built-in types from user-defined ones
    is_system = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="entity_types")
    entities = relationship("Entity", back_populates="entity_type", cascade="all, delete-orphan")
    
    # Unique constraint: each user can only have one entity type with a given name
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_entity_type_name'),
    )


class Entity(Base):
    """
    Represents individual entities in the knowledge graph.
    An entity can be a person, place, organization, concept, etc.
    """
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    entity_type_id = Column(Integer, ForeignKey("entity_types.id"), nullable=False)
    
    # Core fields
    name = Column(String(200), nullable=False)  # e.g., "Elon Musk", "San Francisco"
    description = Column(Text, nullable=True)
    
    # Additional structured data (JSON for flexibility)
    # Can store things like: {"email": "...", "phone": "...", "address": "...", "website": "..."}
    data = Column(JSON, nullable=False, default=dict)
    
    # For entities that represent external references
    external_id = Column(String(100), nullable=True)  # ID from external system
    external_source = Column(String(50), nullable=True)  # e.g., "wikipedia", "linkedin"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="entities")
    entity_type = relationship("EntityType", back_populates="entities")
    
    # Relationships as source entity
    relationships_as_source = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.source_entity_id",
        back_populates="source_entity",
        cascade="all, delete-orphan"
    )
    
    # Relationships as target entity
    relationships_as_target = relationship(
        "EntityRelationship",
        foreign_keys="EntityRelationship.target_entity_id",
        back_populates="target_entity",
        cascade="all, delete-orphan"
    )
    
    # Many-to-many relationships with Goals, Projects, Tasks (defined via association tables)
    # These will be set up in the respective model files


class EntityRelationship(Base):
    """
    Defines relationships between entities in the knowledge graph.
    This creates the edges in the graph structure.
    """
    __tablename__ = "entity_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # The entities involved in the relationship
    source_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    target_entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    
    # The type of relationship
    relationship_type = Column(String(100), nullable=False)  # e.g., "works_at", "located_in", "reports_to"
    
    # Optional metadata about the relationship
    properties = Column(JSON, nullable=False, default=dict)  # e.g., {"since": "2020", "role": "CEO"}
    
    # Relationship strength/weight (for graph algorithms)
    weight = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="entity_relationships")
    source_entity = relationship(
        "Entity",
        foreign_keys=[source_entity_id],
        back_populates="relationships_as_source"
    )
    target_entity = relationship(
        "Entity",
        foreign_keys=[target_entity_id],
        back_populates="relationships_as_target"
    )
    
    # Prevent duplicate relationships
    __table_args__ = (
        UniqueConstraint(
            'user_id', 'source_entity_id', 'target_entity_id', 'relationship_type',
            name='uq_entity_relationship'
        ),
    )


# Performance indexes
Index('ix_entity_types_user_name', EntityType.user_id, EntityType.name)
Index('ix_entity_types_is_system', EntityType.is_system)

Index('ix_entities_user_created', Entity.user_id, Entity.created_at.desc())
Index('ix_entities_user_type', Entity.user_id, Entity.entity_type_id)
Index('ix_entities_user_name', Entity.user_id, Entity.name)
Index('ix_entities_external', Entity.external_source, Entity.external_id)

Index('ix_entity_relationships_user', EntityRelationship.user_id)
Index('ix_entity_relationships_source', EntityRelationship.source_entity_id)
Index('ix_entity_relationships_target', EntityRelationship.target_entity_id)
Index('ix_entity_relationships_type', EntityRelationship.relationship_type)
