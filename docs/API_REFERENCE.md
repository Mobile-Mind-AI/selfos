# SelfOS API Reference

**Version:** v0.2
**Base URL:** `http://localhost:8000/api`
**Authentication:** JWT Bearer Token (Firebase)

## Authentication Endpoints (`auth.py`)

### Register User
`POST /auth/register`
- Creates a new user in Firebase and the local database.

### Login
`POST /auth/login`
- Authenticates a user and returns a JWT.

### Get Current User
`GET /auth/me`
- Returns the currently authenticated user's details.

---

## Core Data Endpoints

### Goals (`goals.py`)
- `GET /goals`: List all goals for the user.
- `POST /goals`: Create a new goal.
- `GET /goals/{goal_id}`: Retrieve a specific goal.
- `PUT /goals/{goal_id}`: Update a goal.
- `DELETE /goals/{goal_id}`: Delete a goal.

### Projects (`projects.py`)
- `GET /projects`: List all projects for the user.
- `POST /projects`: Create a new project.
- `GET /projects/{project_id}`: Retrieve a specific project.
- `PUT /projects/{project_id}`: Update a project.
- `DELETE /projects/{project_id}`: Delete a project.

### Tasks (`tasks.py`)
- `GET /tasks`: List all tasks, with filtering options.
- `POST /tasks`: Create a new task.
- `GET /tasks/{task_id}`: Retrieve a specific task.
- `PUT /tasks/{task_id}`: Update a task.
- `DELETE /tasks/{task_id}`: Delete a task.

### Life Areas (`life_areas.py`)
- `GET /life-areas`: List all life areas.
- `POST /life-areas`: Create a new life area.
- `GET /life-areas/{life_area_id}`: Retrieve a specific life area.
- `PUT /life-areas/{life_area_id}`: Update a life area.
- `DELETE /life-areas/{life_area_id}`: Delete a life area.

### Habits (`habits.py`)
- `GET /habits`: List all habits.
- `POST /habits`: Create a new habit.
- `GET /habits/{habit_id}`: Retrieve a specific habit.
- `PUT /habits/{habit_id}`: Update a habit.
- `DELETE /habits/{habit_id}`: Delete a habit.
- `POST /habits/{habit_id}/log`: Log a completion for a habit.

### Journal (`journal.py`)
- `GET /journal-entries`: List all journal entries.
- `POST /journal-entries`: Create a new journal entry.
- `GET /journal-entries/{entry_id}`: Retrieve a specific entry.
- `PUT /journal-entries/{entry_id}`: Update an entry.
- `DELETE /journal-entries/{entry_id}`: Delete an entry.

### Media Attachments (`media_attachments.py`)
- `GET /media-attachments`: List all media attachments.
- `POST /media-attachments`: Upload a new media file.
- `GET /media-attachments/{attachment_id}`: Retrieve a specific media attachment.
- `DELETE /media-attachments/{attachment_id}`: Delete a media attachment.

### Tags (`tags.py`)
- `GET /tags`: List all tags.
- `POST /tags`: Create a new tag.
- `GET /tags/{tag_id}`: Retrieve a specific tag.
- `DELETE /tags/{tag_id}`: Delete a tag.

---

## AI & Content Generation Endpoints

### AI Services (`ai.py`)
- `POST /ai/decompose-goal`: Break down a goal into tasks using AI.
- `POST /ai/chat`: General chat with the AI assistant.
- `GET /ai/health`: Health check for AI providers.

### Storytelling (`storytelling.py` & `story_sessions.py`)
- `GET /storytelling/recent-stories`: Get recently generated stories.
- `POST /story-sessions`: Create a new story generation session.
- `GET /story-sessions/{session_id}`: Retrieve a story session.
- `POST /story-sessions/{session_id}/generate`: Generate a story from a session.

### Entities (`entities.py`)
- `GET /entities`: List all extracted entities.
- `GET /entities/{entity_id}`: Retrieve a specific entity.

---

## User & System Endpoints

### User Preferences (`user_preferences.py`)
- `GET /users/me/preferences`: Get preferences for the current user.
- `PUT /users/me/preferences`: Update preferences for the current user.

### Assistant Profiles (`assistant_profiles.py`)
- `GET /assistant-profiles`: List available assistant profiles.
- `POST /assistant-profiles`: Create a new assistant profile.

### Onboarding (`onboarding.py`)
- `GET /onboarding/state`: Get the user's current onboarding state.
- `POST /onboarding/complete`: Mark onboarding as complete.

### Analytics (`analytics.py`)
- `GET /analytics/summary`: Get a summary of user activity.

### Progress (`progress.py`)
- `GET /progress/insights`: Get insights into goal and task progress.

### Health (`health.py`)
- `GET /health`: System health check.

---

## Error Responses

- **401 Unauthorized**: Authentication is required.
- **403 Forbidden**: You don't have permission to access this resource.
- **404 Not Found**: The requested resource was not found.
- **422 Unprocessable Entity**: The request body is invalid.
- **500 Internal Server Error**: An unexpected error occurred on the server.

---

*This document provides a high-level overview. For detailed request/response schemas, please refer to the FastAPI-generated documentation at `/docs` when the server is running.*
