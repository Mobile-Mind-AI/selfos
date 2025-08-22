"""
Entity extraction service for automatic detection and extraction
of entities from text using NLP techniques.
"""

import re
from datetime import datetime
from typing import Any

from models import (
    Entity,
    EntityRelationship,
    EntityType,
    Goal,
    GoalEntity,
    Project,
    ProjectEntity,
    Task,
    TaskEntity,
)
from sqlalchemy import or_
from sqlalchemy.orm import Session


class EntityExtractor:
    """Service for extracting and managing entities from text."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self._load_entity_types()
        self._load_existing_entities()

    def _load_entity_types(self):
        """Load available entity types for the user."""
        self.entity_types = {}
        types = (
            self.db.query(EntityType)
            .filter(or_(EntityType.user_id == self.user_id, EntityType.is_system))
            .all()
        )

        for entity_type in types:
            self.entity_types[entity_type.name.lower()] = entity_type

    def _load_existing_entities(self):
        """Load existing entities for matching."""
        self.existing_entities = {}
        entities = (
            self.db.query(Entity)
            .filter(Entity.user_id == self.user_id, Entity.is_active)
            .all()
        )

        for entity in entities:
            # Store by lowercase name for case-insensitive matching
            key = entity.name.lower()
            if key not in self.existing_entities:
                self.existing_entities[key] = []
            self.existing_entities[key].append(entity)

    def extract_entities_from_text(
        self,
        text: str,
        context_type: str | None = None,
        context_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Extract entities from text using pattern matching and NLP.

        Args:
            text: The text to extract entities from
            context_type: Type of context (goal, project, task, conversation)
            context_id: ID of the context item

        Returns:
            List of extracted entities with their details
        """
        extracted_entities = []

        # Extract different types of entities
        extracted_entities.extend(self._extract_people(text))
        extracted_entities.extend(self._extract_places(text))
        extracted_entities.extend(self._extract_organizations(text))
        extracted_entities.extend(self._extract_dates(text))
        extracted_entities.extend(self._extract_urls(text))
        extracted_entities.extend(self._extract_emails(text))
        extracted_entities.extend(self._extract_phone_numbers(text))
        extracted_entities.extend(self._extract_hashtags(text))
        extracted_entities.extend(self._extract_mentions(text))

        # Deduplicate entities
        seen = set()
        unique_entities = []
        for entity in extracted_entities:
            key = (entity["name"].lower(), entity["type"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        # Process and store entities
        processed_entities = []
        for entity_data in unique_entities:
            processed = self._process_entity(entity_data, context_type, context_id)
            if processed:
                processed_entities.append(processed)

        return processed_entities

    def _extract_people(self, text: str) -> list[dict[str, Any]]:
        """Extract person names from text."""
        entities = []

        # Common name patterns
        # Title + Name patterns
        title_pattern = r"\b(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Professor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        for match in re.finditer(title_pattern, text):
            entities.append(
                {
                    "name": match.group(2),
                    "type": "person",
                    "title": match.group(1),
                    "position": match.span(),
                }
            )

        # Capitalized words that could be names (2-3 consecutive capitalized words)
        name_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b"
        for match in re.finditer(name_pattern, text):
            name = match.group(1)
            # Filter out common non-name phrases
            if not self._is_common_phrase(name):
                entities.append(
                    {"name": name, "type": "person", "position": match.span()}
                )

        return entities

    def _extract_places(self, text: str) -> list[dict[str, Any]]:
        """Extract place names from text."""
        entities = []

        # Common place indicators
        place_indicators = [
            "at",
            "in",
            "near",
            "from",
            "to",
            "visit",
            "located",
            "office",
            "building",
            "street",
            "avenue",
            "road",
            "city",
            "country",
            "state",
            "park",
            "restaurant",
            "hotel",
            "airport",
        ]

        # Look for capitalized words after place indicators
        for indicator in place_indicators:
            pattern = rf"\b{indicator}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(
                    {
                        "name": match.group(1),
                        "type": "place",
                        "indicator": indicator,
                        "position": match.span(),
                    }
                )

        return entities

    def _extract_organizations(self, text: str) -> list[dict[str, Any]]:
        """Extract organization names from text."""
        entities = []

        # Common organization patterns
        org_suffixes = [
            "Inc",
            "LLC",
            "Corp",
            "Corporation",
            "Company",
            "Ltd",
            "Limited",
            "Group",
            "Institute",
            "University",
            "College",
            "School",
            "Hospital",
            "Bank",
            "Agency",
        ]

        for suffix in org_suffixes:
            pattern = rf"\b([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\s+{suffix}\.?)\b"
            for match in re.finditer(pattern, text):
                entities.append(
                    {
                        "name": match.group(1),
                        "type": "organization",
                        "position": match.span(),
                    }
                )

        # Acronyms (2-5 capital letters)
        acronym_pattern = r"\b([A-Z]{2,5})\b"
        for match in re.finditer(acronym_pattern, text):
            entities.append(
                {
                    "name": match.group(1),
                    "type": "organization",
                    "subtype": "acronym",
                    "position": match.span(),
                }
            )

        return entities

    def _extract_dates(self, text: str) -> list[dict[str, Any]]:
        """Extract dates and time references from text."""
        entities = []

        # Various date patterns
        date_patterns = [
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",  # MM/DD/YYYY or MM-DD-YYYY
            r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",  # YYYY/MM/DD or YYYY-MM-DD
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
            r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}\b",
            r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
            r"\b(today|tomorrow|yesterday|next\s+week|last\s+week|next\s+month|last\s+month)\b",
        ]

        for pattern in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(
                    {"name": match.group(0), "type": "date", "position": match.span()}
                )

        return entities

    def _extract_urls(self, text: str) -> list[dict[str, Any]]:
        """Extract URLs from text."""
        entities = []
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

        for match in re.finditer(url_pattern, text):
            entities.append(
                {"name": match.group(0), "type": "url", "position": match.span()}
            )

        return entities

    def _extract_emails(self, text: str) -> list[dict[str, Any]]:
        """Extract email addresses from text."""
        entities = []
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        for match in re.finditer(email_pattern, text):
            entities.append(
                {"name": match.group(0), "type": "email", "position": match.span()}
            )

        return entities

    def _extract_phone_numbers(self, text: str) -> list[dict[str, Any]]:
        """Extract phone numbers from text."""
        entities = []

        # Various phone number patterns
        phone_patterns = [
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # XXX-XXX-XXXX
            r"\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b",  # (XXX) XXX-XXXX
            r"\b\+\d{1,3}\s*\d{3,14}\b",  # International format
        ]

        for pattern in phone_patterns:
            for match in re.finditer(pattern, text):
                entities.append(
                    {"name": match.group(0), "type": "phone", "position": match.span()}
                )

        return entities

    def _extract_hashtags(self, text: str) -> list[dict[str, Any]]:
        """Extract hashtags from text."""
        entities = []
        hashtag_pattern = r"#\w+"

        for match in re.finditer(hashtag_pattern, text):
            entities.append(
                {"name": match.group(0), "type": "hashtag", "position": match.span()}
            )

        return entities

    def _extract_mentions(self, text: str) -> list[dict[str, Any]]:
        """Extract @mentions from text."""
        entities = []
        mention_pattern = r"@\w+"

        for match in re.finditer(mention_pattern, text):
            entities.append(
                {"name": match.group(0), "type": "mention", "position": match.span()}
            )

        return entities

    def _is_common_phrase(self, text: str) -> bool:
        """Check if text is a common phrase that shouldn't be treated as an entity."""
        common_phrases = {
            "The",
            "This",
            "That",
            "These",
            "Those",
            "Some",
            "Many",
            "Few",
            "All",
            "Any",
            "Each",
            "Every",
            "No",
            "None",
            "Several",
            "Various",
            "New York",
            "Los Angeles",
            "San Francisco",  # Add common place names
        }
        return text in common_phrases

    def _process_entity(
        self,
        entity_data: dict[str, Any],
        context_type: str | None = None,
        context_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Process extracted entity and store/update in database.

        Returns:
            Processed entity data or None if processing failed
        """
        entity_name = entity_data["name"]
        entity_type_name = entity_data["type"]

        # Get or create entity type
        entity_type = self.entity_types.get(entity_type_name.lower())
        if not entity_type:
            # Create new entity type if it doesn't exist
            entity_type = EntityType(
                user_id=self.user_id,
                name=entity_type_name,
                description=f"Automatically created type for {entity_type_name}",
                is_system=False,
            )
            self.db.add(entity_type)
            self.db.commit()
            self.db.refresh(entity_type)
            self.entity_types[entity_type_name.lower()] = entity_type

        # Check if entity already exists
        existing_key = entity_name.lower()
        existing_entities = self.existing_entities.get(existing_key, [])

        entity = None
        for existing in existing_entities:
            if existing.type_id == entity_type.id:
                entity = existing
                break

        if entity:
            # Update existing entity
            entity.importance = min(1.0, entity.importance + 0.01)
            entity.last_interaction = datetime.utcnow()
        else:
            # Create new entity
            entity = Entity(
                user_id=self.user_id,
                type_id=entity_type.id,
                name=entity_name,
                description=f"Extracted from {context_type or 'text'}",
                attributes=entity_data.get("attributes", {}),
                importance=0.5,
                is_active=True,
            )
            self.db.add(entity)

            # Add to cache
            if existing_key not in self.existing_entities:
                self.existing_entities[existing_key] = []
            self.existing_entities[existing_key].append(entity)

        self.db.commit()
        self.db.refresh(entity)

        # Create association if context is provided
        if context_type and context_id:
            self._create_association(entity.id, context_type, context_id)

        return {
            "id": entity.id,
            "name": entity.name,
            "type": entity_type.name,
            "importance": entity.importance,
            "is_new": entity.created_at == entity.updated_at,
        }

    def _create_association(self, entity_id: int, context_type: str, context_id: int):
        """Create association between entity and context item."""
        if context_type == "goal":
            existing = (
                self.db.query(GoalEntity)
                .filter(
                    GoalEntity.goal_id == context_id, GoalEntity.entity_id == entity_id
                )
                .first()
            )

            if not existing:
                association = GoalEntity(goal_id=context_id, entity_id=entity_id)
                self.db.add(association)

        elif context_type == "project":
            existing = (
                self.db.query(ProjectEntity)
                .filter(
                    ProjectEntity.project_id == context_id,
                    ProjectEntity.entity_id == entity_id,
                )
                .first()
            )

            if not existing:
                association = ProjectEntity(project_id=context_id, entity_id=entity_id)
                self.db.add(association)

        elif context_type == "task":
            existing = (
                self.db.query(TaskEntity)
                .filter(
                    TaskEntity.task_id == context_id, TaskEntity.entity_id == entity_id
                )
                .first()
            )

            if not existing:
                association = TaskEntity(task_id=context_id, entity_id=entity_id)
                self.db.add(association)

        self.db.commit()

    def extract_relationships_from_text(
        self, text: str, entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Extract relationships between entities from text.

        Args:
            text: The text to analyze
            entities: List of entities found in the text

        Returns:
            List of extracted relationships
        """
        relationships = []

        # Relationship indicators
        relationship_patterns = {
            "works_with": ["works with", "collaborates with", "partners with"],
            "reports_to": ["reports to", "managed by", "supervised by"],
            "manages": ["manages", "supervises", "leads"],
            "located_at": ["at", "in", "located at", "based in"],
            "owns": ["owns", "has", "possesses"],
            "belongs_to": ["belongs to", "part of", "member of"],
            "related_to": ["related to", "associated with", "connected to"],
            "meets_with": ["meets with", "meeting with", "scheduled with"],
            "emails": ["emails", "emailed", "sent email to"],
            "calls": ["calls", "called", "phoned"],
        }

        # Look for relationships between entities
        for i, source in enumerate(entities):
            for j, target in enumerate(entities):
                if i >= j:
                    continue  # Avoid duplicates and self-relationships

                # Check if entities appear near each other
                source_pos = text.find(source["name"])
                target_pos = text.find(target["name"])

                if abs(source_pos - target_pos) < 100:  # Within 100 characters
                    # Look for relationship indicators between them
                    start = min(source_pos, target_pos)
                    end = max(source_pos, target_pos) + len(target["name"])
                    segment = text[start:end].lower()

                    for rel_type, indicators in relationship_patterns.items():
                        for indicator in indicators:
                            if indicator in segment:
                                relationships.append(
                                    {
                                        "source_id": source["id"],
                                        "target_id": target["id"],
                                        "type": rel_type,
                                        "indicator": indicator,
                                        "strength": 0.7,
                                    }
                                )
                                break

        # Store relationships in database
        for rel_data in relationships:
            self._create_relationship(rel_data)

        return relationships

    def _create_relationship(self, rel_data: dict[str, Any]):
        """Create or update relationship in database."""
        existing = (
            self.db.query(EntityRelationship)
            .filter(
                EntityRelationship.source_entity_id == rel_data["source_id"],
                EntityRelationship.target_entity_id == rel_data["target_id"],
                EntityRelationship.relationship_type == rel_data["type"],
            )
            .first()
        )

        if existing:
            # Strengthen existing relationship
            existing.strength = min(1.0, existing.strength + 0.1)
            existing.last_interaction = datetime.utcnow()
        else:
            # Create new relationship
            relationship = EntityRelationship(
                source_entity_id=rel_data["source_id"],
                target_entity_id=rel_data["target_id"],
                relationship_type=rel_data["type"],
                strength=rel_data["strength"],
                attributes={"indicator": rel_data.get("indicator")},
            )
            self.db.add(relationship)

        self.db.commit()

    def analyze_entity_importance(self, entity_id: int) -> float:
        """
        Calculate importance score for an entity based on connections and usage.

        Args:
            entity_id: ID of the entity to analyze

        Returns:
            Importance score between 0 and 1
        """
        entity = self.db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return 0.0

        # Factors for importance calculation
        factors = {
            "goal_associations": 0.3,
            "project_associations": 0.25,
            "task_associations": 0.15,
            "relationships": 0.2,
            "recency": 0.1,
        }

        score = 0.0

        # Count associations
        goal_count = (
            self.db.query(GoalEntity).filter(GoalEntity.entity_id == entity_id).count()
        )
        score += min(goal_count * 0.1, factors["goal_associations"])

        project_count = (
            self.db.query(ProjectEntity)
            .filter(ProjectEntity.entity_id == entity_id)
            .count()
        )
        score += min(project_count * 0.05, factors["project_associations"])

        task_count = (
            self.db.query(TaskEntity).filter(TaskEntity.entity_id == entity_id).count()
        )
        score += min(task_count * 0.03, factors["task_associations"])

        # Count relationships
        relationship_count = (
            self.db.query(EntityRelationship)
            .filter(
                or_(
                    EntityRelationship.source_entity_id == entity_id,
                    EntityRelationship.target_entity_id == entity_id,
                )
            )
            .count()
        )
        score += min(relationship_count * 0.02, factors["relationships"])

        # Recency factor
        if entity.last_interaction:
            days_since_interaction = (datetime.utcnow() - entity.last_interaction).days
            if days_since_interaction < 7:
                score += factors["recency"]
            elif days_since_interaction < 30:
                score += factors["recency"] * 0.5
            elif days_since_interaction < 90:
                score += factors["recency"] * 0.2

        return min(score, 1.0)

    def refresh_entity_importance(self, batch_size: int = 100):
        """
        Refresh importance scores for all user entities.

        Args:
            batch_size: Number of entities to process at once
        """
        offset = 0
        while True:
            entities = (
                self.db.query(Entity)
                .filter(Entity.user_id == self.user_id)
                .offset(offset)
                .limit(batch_size)
                .all()
            )

            if not entities:
                break

            for entity in entities:
                new_importance = self.analyze_entity_importance(entity.id)
                entity.importance = new_importance

            self.db.commit()
            offset += batch_size


def extract_entities_from_goal(goal: Goal, db: Session) -> list[dict[str, Any]]:
    """Helper function to extract entities from a goal."""
    extractor = EntityExtractor(db, goal.user_id)

    # Combine title and description for extraction
    text = f"{goal.title} {goal.description or ''}"

    entities = extractor.extract_entities_from_text(
        text, context_type="goal", context_id=goal.id
    )

    # Extract relationships if multiple entities found
    if len(entities) > 1:
        extractor.extract_relationships_from_text(text, entities)

    return entities


# Create service instance for export
class EntityExtractionService:
    """Service wrapper for entity extraction functionality."""

    def extract_from_goal(self, goal: Goal, db: Session) -> list[dict[str, Any]]:
        return extract_entities_from_goal(goal, db)

    def extract_from_project(
        self, project: Project, db: Session
    ) -> list[dict[str, Any]]:
        return extract_entities_from_project(project, db)

    def extract_from_task(self, task: Task, db: Session) -> list[dict[str, Any]]:
        return extract_entities_from_task(task, db)

    def create_extractor(self, db: Session, user_id: str) -> EntityExtractor:
        return EntityExtractor(db, user_id)


# Create singleton instance
entity_extraction_service = EntityExtractionService()


def extract_entities_from_project(
    project: Project, db: Session
) -> list[dict[str, Any]]:
    """Helper function to extract entities from a project."""
    extractor = EntityExtractor(db, project.user_id)

    # Combine name and description for extraction
    text = f"{project.name} {project.description or ''}"

    entities = extractor.extract_entities_from_text(
        text, context_type="project", context_id=project.id
    )

    # Extract relationships if multiple entities found
    if len(entities) > 1:
        extractor.extract_relationships_from_text(text, entities)

    return entities


def extract_entities_from_task(task: Task, db: Session) -> list[dict[str, Any]]:
    """Helper function to extract entities from a task."""
    extractor = EntityExtractor(db, task.user_id)

    # Combine title and description for extraction
    text = f"{task.title} {task.description or ''}"

    entities = extractor.extract_entities_from_text(
        text, context_type="task", context_id=task.id
    )

    # Extract relationships if multiple entities found
    if len(entities) > 1:
        extractor.extract_relationships_from_text(text, entities)

    return entities
