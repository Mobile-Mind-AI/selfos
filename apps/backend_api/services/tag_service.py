"""Tag service for managing user tags and tag associations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, text
from models.tags import Tag
from models.goals import Goal, Project, Task, Habit, JournalEntry
from models.user import User
from schemas import TagCreate, TagUpdate, TagOut
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TagService:
    """Service for managing tags and their associations."""
    
    def __init__(self, db: Session, current_user: Dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.user_id = current_user["uid"]
    
    def create_tag(self, tag_data: TagCreate) -> Tag:
        """Create a new tag for the current user."""
        # Check if tag with same name already exists for this user
        existing_tag = self.db.query(Tag).filter(
            and_(Tag.user_id == self.user_id, Tag.name == tag_data.name)
        ).first()
        
        if existing_tag:
            raise ValueError(f"Tag with name '{tag_data.name}' already exists")
        
        # Create new tag
        db_tag = Tag(
            user_id=self.user_id,
            name=tag_data.name,
            color=tag_data.color,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_tag)
        self.db.commit()
        self.db.refresh(db_tag)
        
        logger.info(f"Created tag '{tag_data.name}' for user {self.user_id}")
        return db_tag
    
    def get_tags(self, include_usage_count: bool = False) -> List[TagOut]:
        """Get all tags for the current user."""
        query = self.db.query(Tag).filter(Tag.user_id == self.user_id)
        tags = query.order_by(Tag.created_at.desc()).all()
        
        if include_usage_count:
            tag_outs = []
            for tag in tags:
                usage_count = self._get_tag_usage_count(tag.id)
                tag_out = TagOut(
                    **tag.__dict__,
                    usage_count=usage_count
                )
                tag_outs.append(tag_out)
            return tag_outs
        else:
            return [TagOut(**tag.__dict__) for tag in tags]
    
    def get_tag_by_id(self, tag_id: int, include_usage_count: bool = False) -> Optional[TagOut]:
        """Get a specific tag by ID."""
        tag = self.db.query(Tag).filter(
            and_(Tag.id == tag_id, Tag.user_id == self.user_id)
        ).first()
        
        if not tag:
            return None
        
        if include_usage_count:
            usage_count = self._get_tag_usage_count(tag_id)
            return TagOut(**tag.__dict__, usage_count=usage_count)
        else:
            return TagOut(**tag.__dict__)
    
    def update_tag(self, tag_id: int, tag_update: TagUpdate) -> Optional[Tag]:
        """Update an existing tag."""
        tag = self.db.query(Tag).filter(
            and_(Tag.id == tag_id, Tag.user_id == self.user_id)
        ).first()
        
        if not tag:
            return None
        
        # Check for name conflicts if name is being updated
        if tag_update.name and tag_update.name != tag.name:
            existing_tag = self.db.query(Tag).filter(
                and_(
                    Tag.user_id == self.user_id,
                    Tag.name == tag_update.name,
                    Tag.id != tag_id
                )
            ).first()
            
            if existing_tag:
                raise ValueError(f"Tag with name '{tag_update.name}' already exists")
        
        # Update fields
        update_data = tag_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tag, field, value)
        
        tag.updated_at = datetime.utcnow()
        tag.version += 1
        
        self.db.commit()
        self.db.refresh(tag)
        
        logger.info(f"Updated tag {tag_id} for user {self.user_id}")
        return tag
    
    def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag and all its associations."""
        tag = self.db.query(Tag).filter(
            and_(Tag.id == tag_id, Tag.user_id == self.user_id)
        ).first()
        
        if not tag:
            return False
        
        # Associations will be automatically deleted due to cascade settings
        self.db.delete(tag)
        self.db.commit()
        
        logger.info(f"Deleted tag {tag_id} for user {self.user_id}")
        return True
    
    def get_tags_by_ids(self, tag_ids: List[int]) -> List[Tag]:
        """Get tags by their IDs (for the current user)."""
        if not tag_ids:
            return []
        
        return self.db.query(Tag).filter(
            and_(Tag.id.in_(tag_ids), Tag.user_id == self.user_id)
        ).all()
    
    def associate_tags_with_entity(self, entity_type: str, entity_id: int, tag_ids: List[int]):
        """Associate tags with an entity (goal, project, task, etc.)."""
        if not tag_ids:
            return
        
        # Get the entity
        entity_map = {
            'goal': Goal,
            'project': Project,
            'task': Task,
            'habit': Habit,
            'journal_entry': JournalEntry
        }
        
        if entity_type not in entity_map:
            raise ValueError(f"Invalid entity type: {entity_type}")
        
        EntityModel = entity_map[entity_type]
        entity = self.db.query(EntityModel).filter(
            and_(EntityModel.id == entity_id, EntityModel.user_id == self.user_id)
        ).first()
        
        if not entity:
            raise ValueError(f"{entity_type.title()} not found")
        
        # Get valid tags
        tags = self.get_tags_by_ids(tag_ids)
        valid_tag_ids = {tag.id for tag in tags}
        invalid_tag_ids = set(tag_ids) - valid_tag_ids
        
        if invalid_tag_ids:
            raise ValueError(f"Invalid tag IDs: {invalid_tag_ids}")
        
        # Set tags (this will replace existing associations)
        entity.tags = tags
        self.db.commit()
        
        logger.info(f"Associated tags {tag_ids} with {entity_type} {entity_id}")
    
    def get_entities_by_tag(self, tag_id: int, entity_types: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Get all entities associated with a specific tag."""
        tag = self.get_tag_by_id(tag_id)
        if not tag:
            return {}
        
        entity_types = entity_types or ['goal', 'project', 'task', 'habit', 'journal_entry']
        
        results = {}
        
        if 'goal' in entity_types:
            goals = self.db.query(Goal).join(Goal.tags).filter(
                and_(Tag.id == tag_id, Goal.user_id == self.user_id)
            ).all()
            results['goals'] = [{'id': g.id, 'title': g.title, 'status': g.status} for g in goals]
        
        if 'project' in entity_types:
            projects = self.db.query(Project).join(Project.tags).filter(
                and_(Tag.id == tag_id, Project.user_id == self.user_id)
            ).all()
            results['projects'] = [{'id': p.id, 'title': p.title, 'status': p.status} for p in projects]
        
        if 'task' in entity_types:
            tasks = self.db.query(Task).join(Task.tags).filter(
                and_(Tag.id == tag_id, Task.user_id == self.user_id)
            ).all()
            results['tasks'] = [{'id': t.id, 'title': t.title, 'status': t.status} for t in tasks]
        
        if 'habit' in entity_types:
            habits = self.db.query(Habit).join(Habit.tags).filter(
                and_(Tag.id == tag_id, Habit.user_id == self.user_id)
            ).all()
            results['habits'] = [{'id': h.id, 'title': h.title, 'is_active': h.is_active} for h in habits]
        
        if 'journal_entry' in entity_types:
            entries = self.db.query(JournalEntry).join(JournalEntry.tags).filter(
                and_(Tag.id == tag_id, JournalEntry.user_id == self.user_id)
            ).all()
            results['journal_entries'] = [{'id': e.id, 'content': e.content[:100] + '...' if len(e.content) > 100 else e.content} for e in entries]
        
        return results
    
    def get_tag_statistics(self) -> Dict[str, Any]:
        """Get statistics about user's tags."""
        total_tags = self.db.query(func.count(Tag.id)).filter(Tag.user_id == self.user_id).scalar()
        
        # Get most used tags
        most_used_tags = []
        tags = self.get_tags(include_usage_count=True)
        for tag in sorted(tags, key=lambda x: x.usage_count or 0, reverse=True)[:5]:
            most_used_tags.append({
                'id': tag.id,
                'name': tag.name,
                'usage_count': tag.usage_count,
                'color': tag.color
            })
        
        return {
            'total_tags': total_tags,
            'most_used_tags': most_used_tags,
            'total_associations': sum(tag.usage_count or 0 for tag in tags)
        }
    
    def _get_tag_usage_count(self, tag_id: int) -> int:
        """Get the total usage count for a tag across all entity types."""
        count = 0
        
        # Count associations with each entity type
        entity_tables = [
            ('project_tags', 'project_id'),
            ('goal_tags', 'goal_id'),
            ('task_tags', 'task_id'),
            ('habit_tags', 'habit_id'),
            ('journal_entry_tags', 'journal_entry_id')
        ]
        
        for table, entity_col in entity_tables:
            result = self.db.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE tag_id = :tag_id"),
                {'tag_id': tag_id}
            ).scalar()
            count += result or 0
        
        return count
    
    def search_tags(self, query: str, limit: int = 10) -> List[TagOut]:
        """Search tags by name."""
        tags = self.db.query(Tag).filter(
            and_(
                Tag.user_id == self.user_id,
                Tag.name.ilike(f'%{query}%')
            )
        ).limit(limit).all()
        
        return [TagOut(**tag.__dict__) for tag in tags]


# Note: TagService requires db and current_user parameters,
# so it cannot be created as a singleton like other services.
# It should be instantiated in the routers when needed.
tag_service = TagService
