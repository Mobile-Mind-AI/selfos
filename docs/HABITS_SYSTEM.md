# SelfOS Habits System Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Models](#data-models)
4. [API Endpoints](#api-endpoints)
5. [Business Logic](#business-logic)
6. [Database Schema](#database-schema)
7. [Testing](#testing)
8. [Usage Examples](#usage-examples)
9. [Integration](#integration)
10. [Performance Considerations](#performance-considerations)

## Overview

The SelfOS Habits System is a comprehensive habit tracking and management solution that allows users to create, monitor, and analyze their daily, weekly, and monthly habits. The system provides streak tracking, progress analytics, and seamless integration with goals and life areas.

### Key Features
- **Flexible Recurrence Patterns**: Daily, weekly, monthly with custom configurations
- **Streak Tracking**: Current and best streak monitoring
- **Progress Analytics**: Completion rates and performance metrics
- **Goal Integration**: Link habits to specific goals and life areas
- **Customization**: Icons, colors, and personalized settings
- **Comprehensive API**: Full CRUD operations with advanced filtering

## Architecture

### Components Structure
```
apps/backend_api/
├── routers/habits.py           # API endpoints
├── services/habit_service.py   # Business logic
├── models/goals.py            # Database models (Habit, HabitCompletion)
├── schemas.py                 # Pydantic validation schemas
├── migrations/add_habits_system.sql  # Database migration
└── tests/
    ├── unit/test_habit_service.py
    └── integration/test_habits_api.py
```

### Technology Stack
- **FastAPI**: REST API framework
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **SQLite/PostgreSQL**: Database backends
- **Pytest**: Testing framework

## Data Models

### Core Models

#### 1. Habit Model
```python
class Habit(Base):
    __tablename__ = "habits"
    
    id: int (Primary Key)
    user_id: str (Foreign Key to users)
    title: str (1-200 characters)
    description: Optional[str] (max 1000 characters)
    recurrence_rule: JSON (RecurrenceRule object)
    is_active: bool (default: True)
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    icon: Optional[str] (max 50 characters)
    color: Optional[str] (hex color, max 50 characters)
    goal_id: Optional[int] (Foreign Key to goals)
    life_area_id: Optional[int] (Foreign Key to life_areas)
    current_streak: int (default: 0)
    best_streak: int (default: 0)
    total_completions: int (default: 0)
    created_at: datetime
    updated_at: datetime
```

#### 2. HabitCompletion Model
```python
class HabitCompletion(Base):
    __tablename__ = "habit_completions"
    
    id: int (Primary Key)
    habit_id: int (Foreign Key to habits)
    completion_date: datetime
    completion_time: datetime
    notes: Optional[str] (max 500 characters)
    duration_minutes: Optional[int] (1-1440)
    intensity_rating: Optional[int] (1-10)
    created_at: datetime
```

#### 3. RecurrenceRule Schema
```python
class RecurrenceRule(BaseModel):
    type: Literal["daily", "weekly", "monthly"]
    target_count: int (1-100)
    target_type: Literal["count"] = "count"
    days_of_week: Optional[List[int]] (0-6, Monday=0)
    days_of_month: Optional[List[int]] (1-31)
```

## API Endpoints

### Base URL: `/api/habits/`

### 1. Create Habit
```http
POST /api/habits/
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Morning Exercise",
  "description": "30 minutes of physical activity every morning",
  "recurrence_rule": {
    "type": "daily",
    "target_count": 1,
    "target_type": "count"
  },
  "start_date": "2025-08-06T00:00:00Z",
  "goal_id": 123,
  "life_area_id": 456,
  "icon": "🏃‍♂️",
  "color": "#4CAF50"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "title": "Morning Exercise",
  "description": "30 minutes of physical activity every morning",
  "recurrence_rule": {
    "type": "daily",
    "target_count": 1,
    "target_type": "count",
    "days_of_week": null,
    "days_of_month": null
  },
  "is_active": true,
  "start_date": "2025-08-06T00:00:00Z",
  "end_date": null,
  "icon": "🏃‍♂️",
  "color": "#4CAF50",
  "goal_id": 123,
  "life_area_id": 456,
  "user_id": "user_123",
  "current_streak": 0,
  "best_streak": 0,
  "total_completions": 0,
  "created_at": "2025-08-05T20:00:00Z",
  "updated_at": "2025-08-05T20:00:00Z"
}
```

### 2. List Habits
```http
GET /api/habits/?active_only=true&limit=20&offset=0
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `active_only` (boolean, optional): Filter only active habits
- `limit` (int, optional): Number of results (default: 50, max: 100)
- `offset` (int, optional): Pagination offset (default: 0)

**Response (200 OK):**
```json
{
  "habits": [
    {
      "id": 1,
      "title": "Morning Exercise",
      // ... full habit object
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### 3. Get Habit by ID
```http
GET /api/habits/{habit_id}
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Morning Exercise",
  // ... all habit fields
  "current_period_progress": {
    "habit_id": 1,
    "period_start": "2025-08-05T00:00:00Z",
    "period_end": "2025-08-06T00:00:00Z",
    "target_count": 1,
    "actual_count": 0,
    "completion_rate": 0.0,
    "is_completed": false,
    "completions": []
  },
  "recent_completions": [],
  "goal": null,
  "life_area": null
}
```

### 4. Update Habit
```http
PUT /api/habits/{habit_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:** (All fields optional)
```json
{
  "title": "Updated Morning Exercise",
  "is_active": false,
  "recurrence_rule": {
    "type": "weekly",
    "target_count": 5,
    "target_type": "count",
    "days_of_week": [0, 1, 2, 3, 4]
  }
}
```

### 5. Delete Habit
```http
DELETE /api/habits/{habit_id}
Authorization: Bearer <jwt_token>
```

**Response (204 No Content)**

### 6. Complete Habit
```http
POST /api/habits/{habit_id}/complete
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:** (All fields optional)
```json
{
  "completion_date": "2025-08-06T08:00:00Z",
  "notes": "Great morning workout!",
  "duration_minutes": 30,
  "intensity_rating": 8
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "habit_id": 1,
  "completion_date": "2025-08-06T08:00:00Z",
  "completion_time": "2025-08-06T08:00:00Z",
  "notes": "Great morning workout!",
  "duration_minutes": 30,
  "intensity_rating": 8,
  "created_at": "2025-08-06T08:00:00Z"
}
```

### 7. Get Habit Completions
```http
GET /api/habits/{habit_id}/completions?limit=30&offset=0
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `limit` (int, optional): Number of results (default: 50)
- `offset` (int, optional): Pagination offset (default: 0)

### 8. Get Habit Progress
```http
GET /api/habits/{habit_id}/progress?period_start=2025-08-01&period_end=2025-08-31
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `period_start` (datetime, optional): Start of analysis period
- `period_end` (datetime, optional): End of analysis period

## Business Logic

### HabitService Class

The `HabitService` class encapsulates all business logic for habit management:

#### Key Methods

##### 1. `create_habit(db, user_id, habit_data)`
- Validates habit data
- Creates habit record with initial statistics
- Sets start_date to today if not provided
- Returns created habit

##### 2. `get_habits(db, user_id, active_only, limit, offset)`
- Retrieves user's habits with pagination
- Filters by active status if requested
- Returns paginated results

##### 3. `complete_habit(db, user_id, habit_id, completion_data)`
- Prevents duplicate completions on same date
- Creates completion record
- Updates habit statistics (streaks, total completions)
- Returns completion record

##### 4. `get_habit_progress(db, user_id, habit_id, period_start, period_end)`
- Calculates progress for specified period
- Determines current period based on recurrence rule
- Returns progress statistics and completion list

##### 5. `_calculate_current_streak(db, habit)`
- Analyzes completion history
- Calculates consecutive completion streak
- Returns current streak count

##### 6. `_update_habit_stats(db, habit)`
- Updates current_streak and best_streak
- Increments total_completions
- Commits changes to database

### Recurrence Logic

#### Daily Habits
- Period: Single day (00:00 - 23:59)
- Target: Configurable count per day
- Streak: Consecutive days with target met

#### Weekly Habits
- Period: Monday to Sunday
- Target: Configurable count per week
- Optional: Specific days of week
- Streak: Consecutive weeks with target met

#### Monthly Habits
- Period: First to last day of month
- Target: Configurable count per month
- Optional: Specific days of month
- Streak: Consecutive months with target met

### Streak Calculation Algorithm

```python
def _calculate_current_streak(self, db: Session, habit: models.Habit) -> int:
    # Get all completions ordered by date DESC
    completions = db.query(models.HabitCompletion)\
        .filter(models.HabitCompletion.habit_id == habit.id)\
        .order_by(models.HabitCompletion.completion_date.desc())\
        .all()
    
    if not completions:
        return 0
    
    streak = 0
    current_date = datetime.utcnow().date()
    
    # Check each period working backwards
    while True:
        period_start, period_end = self._get_period_bounds(
            habit.recurrence_rule["type"], current_date
        )
        
        # Count completions in this period
        period_completions = [
            c for c in completions 
            if period_start <= c.completion_date.date() <= period_end
        ]
        
        # Check if target was met
        if len(period_completions) >= habit.recurrence_rule["target_count"]:
            streak += 1
            current_date = period_start - timedelta(days=1)
        else:
            break
    
    return streak
```

## Database Schema

### Tables

#### habits
```sql
CREATE TABLE habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    recurrence_rule JSON NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    start_date DATETIME,
    end_date DATETIME,
    icon VARCHAR(50),
    color VARCHAR(50),
    goal_id INTEGER,
    life_area_id INTEGER,
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    total_completions INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE SET NULL,
    FOREIGN KEY (life_area_id) REFERENCES life_areas(id) ON DELETE SET NULL
);
```

#### habit_completions
```sql
CREATE TABLE habit_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    completion_date DATETIME NOT NULL,
    completion_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    duration_minutes INTEGER,
    intensity_rating INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    UNIQUE(habit_id, completion_date)
);
```

### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_habits_user_id ON habits(user_id);
CREATE INDEX idx_habits_active ON habits(is_active);
CREATE INDEX idx_habit_completions_habit_id ON habit_completions(habit_id);
CREATE INDEX idx_habit_completions_date ON habit_completions(completion_date);
CREATE INDEX idx_habit_completions_habit_date ON habit_completions(habit_id, completion_date);
```

## Testing

### Test Coverage

#### Unit Tests (21/22 passing)
- **test_habit_service.py**: Tests all HabitService methods
- **Coverage**: 95%+ of business logic
- **Scenarios**: Success cases, error handling, edge cases

#### Integration Tests (22/22 passing)
- **test_habits_api.py**: Tests all API endpoints
- **Coverage**: Full API surface
- **Scenarios**: CRUD operations, validation, user isolation

### Test Examples

#### Unit Test Example
```python
def test_create_habit_success(self):
    """Test successful habit creation"""
    habit_data = schemas.HabitCreate(
        title="Test Habit",
        recurrence_rule=schemas.RecurrenceRule(
            type="daily",
            target_count=1,
            target_type="count"
        )
    )
    
    result = self.habit_service.create_habit(
        self.mock_db, self.user_id, habit_data
    )
    
    assert result.title == "Test Habit"
    assert result.current_streak == 0
    assert result.total_completions == 0
```

#### Integration Test Example
```python
def test_complete_habit_success(self, client, auth_headers):
    """Test successful habit completion"""
    # Create habit
    habit_response = client.post("/api/habits/", json={
        "title": "Test Habit",
        "recurrence_rule": {
            "type": "daily",
            "target_count": 1,
            "target_type": "count"
        }
    }, headers=auth_headers)
    
    habit_id = habit_response.json()["id"]
    
    # Complete habit
    completion_response = client.post(
        f"/api/habits/{habit_id}/complete",
        json={"notes": "Done!"},
        headers=auth_headers
    )
    
    assert completion_response.status_code == 201
    assert completion_response.json()["notes"] == "Done!"
```

## Usage Examples

### Frontend Integration

#### Creating a Daily Exercise Habit
```typescript
const createHabit = async () => {
  const response = await fetch('/api/habits/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title: 'Daily Exercise',
      description: '30 minutes of physical activity',
      recurrence_rule: {
        type: 'daily',
        target_count: 1,
        target_type: 'count'
      },
      icon: '🏃‍♂️',
      color: '#4CAF50',
      goal_id: goalId
    })
  });
  
  return response.json();
};
```

#### Completing a Habit
```typescript
const completeHabit = async (habitId: number) => {
  const response = await fetch(`/api/habits/${habitId}/complete`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      notes: 'Great session today!',
      duration_minutes: 30,
      intensity_rating: 8
    })
  });
  
  return response.json();
};
```

#### Fetching Habit Progress
```typescript
const getHabitProgress = async (habitId: number) => {
  const response = await fetch(
    `/api/habits/${habitId}/progress?period_start=2025-08-01&period_end=2025-08-31`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  return response.json();
};
```

### Mobile App Integration

#### React Native Example
```typescript
import { useHabits } from './hooks/useHabits';

const HabitsScreen = () => {
  const { habits, loading, completeHabit } = useHabits();
  
  const handleComplete = async (habitId: number) => {
    try {
      await completeHabit(habitId, {
        notes: 'Completed on mobile!',
        duration_minutes: 15
      });
      // Update UI
    } catch (error) {
      console.error('Failed to complete habit:', error);
    }
  };
  
  return (
    <View>
      {habits.map(habit => (
        <HabitCard 
          key={habit.id}
          habit={habit}
          onComplete={() => handleComplete(habit.id)}
        />
      ))}
    </View>
  );
};
```

## Integration

### Goal Integration
Habits can be linked to goals for comprehensive progress tracking:

```python
# Create habit linked to goal
habit = await habit_service.create_habit(db, user_id, HabitCreate(
    title="Read Daily",
    goal_id=reading_goal.id,
    recurrence_rule=RecurrenceRule(type="daily", target_count=1)
))

# Goal progress includes habit completions
goal_progress = await goal_service.get_progress(db, user_id, reading_goal.id)
# goal_progress.habits_contribution = 25%
```

### Life Areas Integration
Habits contribute to life area balance and tracking:

```python
# Create habit in Health life area
habit = await habit_service.create_habit(db, user_id, HabitCreate(
    title="Morning Workout",
    life_area_id=health_area.id,
    recurrence_rule=RecurrenceRule(type="daily", target_count=1)
))

# Life area analytics include habit data
life_area_stats = await life_area_service.get_analytics(db, user_id, health_area.id)
# life_area_stats.active_habits_count = 3
# life_area_stats.completion_rate = 0.85
```

### Notification Integration
Habits can trigger reminders and notifications:

```python
# Check for habits due today
due_habits = await habit_service.get_due_habits(db, user_id, date.today())

# Send notifications
for habit in due_habits:
    await notification_service.send_habit_reminder(
        user_id=user_id,
        habit_id=habit.id,
        message=f"Time for your {habit.title}!"
    )
```

## Performance Considerations

### Database Optimization

#### Indexing Strategy
- Primary indexes on user_id for data isolation
- Composite indexes on frequently queried combinations
- Date indexes for completion queries and analytics

#### Query Optimization
```python
# Efficient habit listing with pagination
def get_habits_optimized(db, user_id, active_only=None, limit=50, offset=0):
    query = db.query(models.Habit)\
        .filter(models.Habit.user_id == user_id)
    
    if active_only is not None:
        query = query.filter(models.Habit.is_active == active_only)
    
    return query.order_by(models.Habit.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()
```

#### Bulk Operations
```python
# Efficient streak calculation for multiple habits
def update_all_streaks(db, user_id):
    habits = db.query(models.Habit)\
        .filter(models.Habit.user_id == user_id)\
        .filter(models.Habit.is_active == True)\
        .all()
    
    # Batch process streaks
    for habit in habits:
        new_streak = self._calculate_current_streak(db, habit)
        habit.current_streak = new_streak
        habit.best_streak = max(habit.best_streak, new_streak)
    
    db.commit()
```

### Caching Strategy

#### Redis Caching
```python
# Cache frequently accessed habit data
@cached(ttl=300)  # 5 minutes
async def get_habit_with_cache(habit_id: int, user_id: str):
    return await habit_service.get_habit(db, user_id, habit_id)

# Cache completion status
@cached(ttl=3600)  # 1 hour
async def is_habit_completed_today(habit_id: int):
    return await habit_service.is_completed_today(db, habit_id)
```

### API Rate Limiting
```python
# Rate limit habit completion to prevent abuse
@rate_limit("habit_complete", max_calls=10, period=60)
async def complete_habit(habit_id: int, completion_data: HabitCompletionCreate):
    return await habit_service.complete_habit(db, user_id, habit_id, completion_data)
```

### Memory Optimization
- Pagination for large datasets
- Lazy loading of related entities
- Efficient JSON serialization
- Connection pooling for database operations

This comprehensive habits system provides a robust foundation for habit tracking within the SelfOS ecosystem, with full API coverage, thorough testing, and optimization for performance and scalability.
