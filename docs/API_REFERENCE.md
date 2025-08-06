# SelfOS API Reference

**Version:** v0.1  
**Base URL:** `http://localhost:8000/api`  
**Authentication:** JWT Bearer Token

## Authentication Endpoints

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true
  }
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com", 
  "password": "securepassword"
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer {access_token}
```

## Goals Management

### List Goals
```http
GET /goals
Authorization: Bearer {access_token}
```

### Create Goal
```http
POST /goals
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Learn Guitar",
  "description": "Master basic guitar skills",
  "target_date": "2025-12-31",
  "life_area_id": "uuid"
}
```

### Update Goal
```http
PUT /goals/{goal_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Learn Guitar - Updated",
  "status": "in_progress"
}
```

### Get Goals by Life Area
```http
GET /goals/life-area/{life_area_id}
Authorization: Bearer {access_token}
```

### Get Goals by Status
```http
GET /goals/status/{status}
Authorization: Bearer {access_token}
```

### Delete Goal
```http
DELETE /goals/{goal_id}
Authorization: Bearer {access_token}
```

## Tasks Management

### List Tasks
```http
GET /tasks
Authorization: Bearer {access_token}
Query Parameters:
- goal_id: Filter by goal ID
- status: Filter by status (pending, in_progress, completed)
```

### Create Task
```http
POST /tasks
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Practice scales",
  "description": "Practice major and minor scales",
  "goal_id": "uuid",
  "due_date": "2025-07-15"
}
```

### Update Task
```http
PUT /tasks/{task_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "status": "completed",
  "completed_at": "2025-06-30T10:00:00Z"
}
```

### Mark Task Complete
```http
PUT /tasks/{task_id}/complete
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Practice scales",
  "status": "completed",
  "progress": 100.0,
  "completed_at": "2025-07-01T10:00:00Z"
}
```

### Get Tasks by Goal
```http
GET /tasks/goal/{goal_id}
Authorization: Bearer {access_token}
```

### Get Tasks by Status
```http
GET /tasks/status/{status}
Authorization: Bearer {access_token}
```

### Delete Task
```http
DELETE /tasks/{task_id}
Authorization: Bearer {access_token}
```

## Progress Analytics

### Get Progress Insights
```http
GET /progress/insights
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "total_goals": 5,
  "completed_goals": 2,
  "goal_completion_rate": 40.0,
  "total_tasks": 25,
  "completed_tasks": 12,
  "task_completion_rate": 48.0,
  "weekly_velocity": 3,
  "monthly_velocity": 12,
  "most_productive_area": "Health",
  "recommendations": [
    "Consider breaking down your current tasks into smaller, achievable steps",
    "Try to complete at least one task per day to maintain momentum"
  ],
  "last_updated": "2025-07-01T10:00:00Z"
}
```

### Get Goal Completion Prediction
```http
GET /progress/goals/{goal_id}/prediction
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "goal_id": 123,
  "predicted_completion_date": "2025-08-15T00:00:00Z",
  "reason": "Prediction based on recent task completion velocity"
}
```

### Get Progress Summary
```http
GET /progress/summary
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "total_goals": 5,
  "completed_goals": 2,
  "goal_completion_rate": 40.0,
  "total_tasks": 25,
  "completed_tasks": 12,
  "task_completion_rate": 48.0,
  "weekly_velocity": 3,
  "most_productive_area": "Health",
  "top_recommendation": "Consider breaking down your current tasks into smaller, achievable steps",
  "last_updated": "2025-07-01T10:00:00Z"
}
```

## Storytelling & Narratives

### Get Weekly Summary
```http
GET /storytelling/weekly-summary
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "story_text": "This week brought 3 accomplishments across different areas of focus. In one area, 'Practice guitar scales' was completed successfully. Significant progress was made with tasks including 'Morning workout routine' and 1 other achievements. Each completion builds toward larger objectives and represents meaningful progress in the journey of personal development.",
  "task_count": 3,
  "areas_involved": 2,
  "week_period": "Last 7 days",
  "generated_at": "2025-07-01T10:00:00Z"
}
```

### Generate Story Prompts
```http
POST /storytelling/prompts
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Learn Guitar",
  "description": "Master basic guitar skills",
  "life_area_id": "uuid",
  "media_count": 2
}
```

**Response:**
```json
{
  "task_title": "Learn Guitar",
  "prompts": [
    "Write an inspiring story about completing 'Learn Guitar'. Focus on the sense of accomplishment and progress.",
    "Create a narrative about the journey of completing 'Learn Guitar'. Include details about: Master basic guitar skills",
    "Tell the story of 'Learn Guitar' completion, incorporating visual elements and media that documented the process.",
    "Write about how completing 'Learn Guitar' contributes to overall growth in this life area.",
    "Describe the personal growth achieved through completing 'Learn Guitar', emphasizing lessons learned and future potential."
  ],
  "prompt_count": 5,
  "usage_note": "These prompts can be used with AI language models to generate personalized achievement stories"
}
```

### Get Recent Stories
```http
GET /storytelling/recent-stories?limit=10
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "stories": [
    {
      "id": "uuid",
      "title": "Completed: Practice scales",
      "generated_text": "Today marks a significant milestone: Practice scales has been successfully completed!...",
      "summary_period": "task-based",
      "content_type": "achievement",
      "word_count": 85,
      "estimated_read_time": 340,
      "generated_at": "2025-07-01T10:00:00Z",
      "processing_status": "completed",
      "source_tasks_count": 1,
      "source_goals_count": 1
    }
  ],
  "total_count": 1,
  "limit": 10
}
```

### Get Story Details
```http
GET /storytelling/stories/{story_id}
Authorization: Bearer {access_token}
```

### Delete Story
```http
DELETE /storytelling/stories/{story_id}
Authorization: Bearer {access_token}
```

## AI Services

### Decompose Goal
```http
POST /ai/decompose-goal
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "goal_description": "I want to learn guitar",
  "context": {
    "user_preferences": ["acoustic", "beginner"],
    "time_available": "1 hour daily"
  }
}
```

**Response:**
```json
{
  "tasks": [
    {
      "title": "Get a guitar",
      "description": "Purchase or borrow an acoustic guitar",
      "priority": "high",
      "estimated_duration": "1 day"
    },
    {
      "title": "Learn basic chords",
      "description": "Master A, D, E, G, C chords",
      "priority": "high", 
      "estimated_duration": "2 weeks"
    }
  ],
  "timeline": "3-6 months",
  "difficulty": "beginner"
}
```

### Chat with AI
```http
POST /ai/chat
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "How do I stay motivated with my goals?",
  "conversation_id": "uuid",
  "user_context": {
    "current_goals": ["learn guitar", "get fit"],
    "emotional_state": "discouraged"
  }
}
```

**Response:**
```json
{
  "response": "I understand feeling discouraged is normal...",
  "conversation_id": "uuid",
  "suggestions": [
    "Break down large goals into smaller tasks",
    "Celebrate small wins along the way"
  ]
}
```

### AI Health Check
```http
GET /ai/health
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "status": "healthy",
  "providers": {
    "openai": "healthy",
    "anthropic": "healthy",
    "local": "healthy"
  },
  "response_time_ms": 150
}
```

## Error Responses

All endpoints may return these common error responses:

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limits

- **Authentication endpoints**: 5 requests per minute
- **AI endpoints**: 10 requests per minute  
- **CRUD endpoints**: 100 requests per minute

## SDKs and Libraries

### Python
```python
import requests

class SelfOSClient:
    def __init__(self, base_url="http://localhost:8000/api", token=None):
        self.base_url = base_url
        self.token = token
        
    def login(self, email, password):
        response = requests.post(f"{self.base_url}/auth/login", 
                               json={"email": email, "password": password})
        self.token = response.json()["access_token"]
        return response.json()
        
    def create_goal(self, title, description):
        headers = {"Authorization": f"Bearer {self.token}"}
        return requests.post(f"{self.base_url}/goals",
                           json={"title": title, "description": description},
                           headers=headers).json()
```

### JavaScript
```javascript
class SelfOSClient {
  constructor(baseURL = 'http://localhost:8000/api', token = null) {
    this.baseURL = baseURL;
    this.token = token;
  }
  
  async login(email, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await response.json();
    this.token = data.access_token;
    return data;
  }
  
  async createGoal(title, description) {
    return fetch(`${this.baseURL}/goals`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify({ title, description })
    }).then(r => r.json());
  }
}
```

## Webhooks (Planned)

Future webhook support for real-time notifications:

### Goal Completed
```json
{
  "event": "goal.completed",
  "data": {
    "goal_id": "uuid",
    "user_id": "uuid",
    "completed_at": "2025-06-30T10:00:00Z"
  }
}
```

### Task Due Soon
```json
{
  "event": "task.due_soon", 
  "data": {
    "task_id": "uuid",
    "due_date": "2025-07-01T10:00:00Z",
    "hours_remaining": 24
  }
}
```

---

For more information and examples, see the [Development Guide](DEVELOPMENT.md) and [Getting Started](GETTING_STARTED.md) documentation.
