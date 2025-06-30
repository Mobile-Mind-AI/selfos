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

### Delete Task
```http
DELETE /tasks/{task_id}
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