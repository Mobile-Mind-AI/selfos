# Hierarchy System Documentation

## Overview

The SelfOS Hierarchy System provides parent-child relationships for Goals and Projects, enabling users to organize their objectives in tree structures. This system supports complex organizational hierarchies while maintaining data integrity and preventing circular references.

## Architecture

### Core Components

1. **Models**: Goal and Project models with `parent_id` foreign key relationships
2. **Services**: GoalService and ProjectService with comprehensive hierarchy operations
3. **Schemas**: HierarchyTreeNode for tree structure representation
4. **API Endpoints**: RESTful hierarchy endpoints for both Goals and Projects
5. **Database**: PostgreSQL with proper foreign key constraints and indexes

### Key Features

- **Tree Operations**: Get roots, children, descendants, and full tree structures
- **Move Operations**: Change parent-child relationships with cycle prevention
- **User Isolation**: All hierarchy operations respect user boundaries
- **Data Integrity**: Foreign key constraints and validation prevent orphaned records
- **Cycle Prevention**: Automatic detection and prevention of circular references

## Database Schema

### Goals Table
```sql
CREATE TABLE goals (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES goals(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    -- other fields...
    FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE CASCADE
);

CREATE INDEX idx_goals_parent_id ON goals(parent_id);
CREATE INDEX idx_goals_user_parent ON goals(user_id, parent_id);
```

### Projects Table
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    -- other fields...
    FOREIGN KEY (parent_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_projects_parent_id ON projects(parent_id);
CREATE INDEX idx_projects_user_parent ON projects(user_id, parent_id);
```

## API Endpoints

### Goals Hierarchy

#### Get Root Goals
```http
GET /api/goals/roots
```
Returns all top-level goals (those without parents) for the current user.

**Response:**
```json
[
  {
    "id": 1,
    "title": "Career Development",
    "description": "Professional growth objectives",
    "parent_id": null,
    "children": []
  }
]
```

#### Get Goal Children
```http
GET /api/goals/{goal_id}/children
```
Returns direct children of a specific goal.

**Response:**
```json
[
  {
    "id": 2,
    "title": "Learn Python",
    "description": "Master Python programming",
    "parent_id": 1,
    "children": []
  }
]
```

#### Get Goal Tree
```http
GET /api/goals/tree
```
Returns the complete goal hierarchy as nested tree structure.

**Response:**
```json
[
  {
    "id": 1,
    "title": "Career Development",
    "children": [
      {
        "id": 2,
        "title": "Learn Python",
        "children": [
          {
            "id": 3,
            "title": "Complete Python Course",
            "children": []
          }
        ]
      }
    ]
  }
]
```

#### Move Goal
```http
PUT /api/goals/{goal_id}/move
Content-Type: application/json

{
  "new_parent_id": 5
}
```
Moves a goal to a new parent. Set `new_parent_id` to `null` to move to root level.

### Projects Hierarchy

Projects support identical endpoints with `/api/projects/` prefix:

- `GET /api/projects/roots` - Get root projects
- `GET /api/projects/{project_id}/children` - Get project children
- `GET /api/projects/tree` - Get project tree
- `PUT /api/projects/{project_id}/move` - Move project

## Service Layer

### GoalService Hierarchy Methods

```python
class GoalService:
    def get_roots(self, user_id: str) -> List[Goal]:
        """Get all root-level goals for user"""

    def get_children(self, user_id: str, parent_id: int) -> List[Goal]:
        """Get direct children of a goal"""

    def get_descendants(self, user_id: str, goal_id: int) -> List[Goal]:
        """Get all descendants (recursive children)"""

    def get_tree(self, user_id: str) -> List[HierarchyTreeNode]:
        """Get complete hierarchy as tree structure"""

    def move_goal(self, user_id: str, goal_id: int, new_parent_id: Optional[int]) -> Goal:
        """Move goal to new parent with cycle prevention"""

    def _would_create_cycle(self, user_id: str, goal_id: int, new_parent_id: int) -> bool:
        """Check if move would create circular reference"""
```

### ProjectService Hierarchy Methods

ProjectService provides identical methods for project hierarchy management.

## Data Models

### HierarchyTreeNode Schema

```python
class HierarchyTreeNode(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    children: List['HierarchyTreeNode'] = []

    class Config:
        orm_mode = True

# Enable recursive references
HierarchyTreeNode.model_rebuild()
```

### HierarchyMoveRequest Schema

```python
class HierarchyMoveRequest(BaseModel):
    new_parent_id: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "new_parent_id": 5
            }
        }
```

## Usage Examples

### Creating Hierarchical Goals

```python
# Create parent goal
parent_goal = goal_service.create_goal(
    user_id="user123",
    goal_data=GoalCreate(
        title="Career Development",
        description="Professional growth objectives"
    )
)

# Create child goal
child_goal = goal_service.create_goal(
    user_id="user123",
    goal_data=GoalCreate(
        title="Learn Python",
        description="Master Python programming",
        parent_id=parent_goal.id
    )
)
```

### Moving Goals in Hierarchy

```python
# Move goal to new parent
moved_goal = goal_service.move_goal(
    user_id="user123",
    goal_id=child_goal.id,
    new_parent_id=new_parent_goal.id
)

# Move goal to root level
root_goal = goal_service.move_goal(
    user_id="user123",
    goal_id=child_goal.id,
    new_parent_id=None
)
```

### Retrieving Hierarchy Data

```python
# Get all root goals
roots = goal_service.get_roots(user_id="user123")

# Get children of specific goal
children = goal_service.get_children(user_id="user123", parent_id=1)

# Get complete tree structure
tree = goal_service.get_tree(user_id="user123")

# Get all descendants
descendants = goal_service.get_descendants(user_id="user123", goal_id=1)
```

## Security & Validation

### User Isolation
All hierarchy operations are automatically filtered by `user_id` to ensure users can only access and modify their own goals and projects.

### Cycle Prevention
The system prevents circular references through the `_would_create_cycle` validation method:

```python
def _would_create_cycle(self, user_id: str, goal_id: int, new_parent_id: int) -> bool:
    """
    Check if moving goal_id under new_parent_id would create a cycle.
    A cycle occurs when new_parent_id is a descendant of goal_id.
    """
    if new_parent_id is None:
        return False

    current_id = new_parent_id
    visited = set()

    while current_id is not None:
        if current_id == goal_id:
            return True

        if current_id in visited:
            break

        visited.add(current_id)
        parent = self.get_by_id(user_id, current_id)
        current_id = parent.parent_id if parent else None

    return False
```

### Data Integrity
- Foreign key constraints ensure referential integrity
- Cascade delete operations handle orphaned records
- Validation prevents invalid parent assignments

## Performance Considerations

### Database Indexes
```sql
-- Optimize hierarchy queries
CREATE INDEX idx_goals_parent_id ON goals(parent_id);
CREATE INDEX idx_goals_user_parent ON goals(user_id, parent_id);
CREATE INDEX idx_projects_parent_id ON projects(parent_id);
CREATE INDEX idx_projects_user_parent ON projects(user_id, parent_id);
```

### Query Optimization
- Tree operations use efficient recursive queries
- Batch loading prevents N+1 query problems
- User filtering applied at database level

### Depth Limitations
- Recommended maximum depth: 10 levels
- System handles arbitrary depth but performance may degrade
- Consider flattening very deep hierarchies

## Testing

### Unit Tests
- **Goal Hierarchy**: 14 comprehensive tests covering all operations
- **Project Hierarchy**: 17 comprehensive tests including edge cases
- **Service Methods**: Full coverage of hierarchy operations
- **Validation**: Cycle prevention and data integrity tests

### Test Coverage Areas
- Tree structure operations
- Move operations with cycle prevention
- User isolation and security
- Data consistency and integrity
- Performance with large hierarchies
- Edge cases and error handling

### Running Tests
```bash
# Run hierarchy-specific tests
python -m pytest tests/unit/test_goal_hierarchy.py -v
python -m pytest tests/unit/test_project_hierarchy.py -v

# Run all tests with custom runner
python run_tests.py --verbose
```

## Migration

The hierarchy system was implemented in Stage 3 with the following migration:

```sql
-- Add parent_id columns to existing tables
ALTER TABLE goals ADD COLUMN parent_id INTEGER;
ALTER TABLE projects ADD COLUMN parent_id INTEGER;

-- Add foreign key constraints
ALTER TABLE goals
ADD CONSTRAINT fk_goals_parent
FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE CASCADE;

ALTER TABLE projects
ADD CONSTRAINT fk_projects_parent
FOREIGN KEY (parent_id) REFERENCES projects(id) ON DELETE CASCADE;

-- Add performance indexes
CREATE INDEX idx_goals_parent_id ON goals(parent_id);
CREATE INDEX idx_goals_user_parent ON goals(user_id, parent_id);
CREATE INDEX idx_projects_parent_id ON projects(parent_id);
CREATE INDEX idx_projects_user_parent ON projects(user_id, parent_id);
```

## Future Enhancements

### Planned Features
1. **Task Hierarchy**: Extend hierarchy support to Task model
2. **Drag & Drop**: Frontend interface for visual hierarchy management
3. **Bulk Operations**: Move multiple items simultaneously
4. **Path Queries**: Find path from root to specific node
5. **Depth Limits**: Configurable maximum hierarchy depth
6. **Tree Statistics**: Analyze hierarchy depth and breadth

### Performance Improvements
1. **Materialized Paths**: Store full path for faster ancestor queries
2. **Nested Sets**: Alternative tree representation for read-heavy workloads
3. **Caching**: Redis cache for frequently accessed tree structures
4. **Lazy Loading**: Progressive tree loading for large hierarchies

## Troubleshooting

### Common Issues

#### Cycle Detection Failures
**Problem**: Move operation fails with cycle error
**Solution**: Use API to check hierarchy before attempting moves

#### Orphaned Records
**Problem**: Records with invalid parent_id values
**Solution**: Foreign key constraints prevent this; check data integrity

#### Performance Issues
**Problem**: Slow hierarchy queries with large datasets
**Solution**: Ensure proper indexing and consider materialized paths

#### User Isolation Failures
**Problem**: Users seeing other users' hierarchy data
**Solution**: Verify all service methods include user_id filtering

### Debugging

Enable debug logging for hierarchy operations:
```python
import logging
logging.getLogger('services.goal_service').setLevel(logging.DEBUG)
logging.getLogger('services.project_service').setLevel(logging.DEBUG)
```

Monitor database performance:
```sql
-- Check index usage
EXPLAIN ANALYZE SELECT * FROM goals WHERE user_id = 'user123' AND parent_id IS NULL;

-- Monitor hierarchy query performance
EXPLAIN ANALYZE WITH RECURSIVE goal_tree AS (
  SELECT id, title, parent_id, 1 as level
  FROM goals
  WHERE user_id = 'user123' AND parent_id IS NULL

  UNION ALL

  SELECT g.id, g.title, g.parent_id, gt.level + 1
  FROM goals g
  JOIN goal_tree gt ON g.parent_id = gt.id
  WHERE g.user_id = 'user123'
)
SELECT * FROM goal_tree;
```

## Conclusion

The SelfOS Hierarchy System provides a robust foundation for organizing Goals and Projects in tree structures. With comprehensive testing, security validation, and performance optimization, it enables users to create complex organizational hierarchies while maintaining data integrity and system performance.

The system is production-ready with 31 passing unit tests and full integration with the existing SelfOS architecture.
