from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, time

## Authentication Schemas
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class User(BaseModel):
    uid: str = Field(..., description="Firebase user ID")
    email: str = Field(..., description="User email address")

class GoalBase(BaseModel):
    title: str = Field(..., description="Title of the goal")
    description: Optional[str] = Field(None, description="Detailed description of the goal")
    status: Optional[str] = Field('todo', description="Status of the goal (todo, in_progress, completed)")
    progress: Optional[float] = Field(0.0, description="Progress percentage of the goal")
    life_area_id: Optional[int] = Field(None, description="Associated life area ID")

class GoalCreate(GoalBase):
    """Schema for creating a new Goal"""
    pass

class Goal(GoalBase):
    id: int = Field(..., description="Unique goal ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        orm_mode = True

class TaskBase(BaseModel):
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description of the task")
    due_date: Optional[datetime] = Field(None, description="Optional due date for the task")
    duration: Optional[int] = Field(None, description="Expected duration in minutes")
    status: Optional[str] = Field('todo', description="Status of the task")
    progress: Optional[float] = Field(0.0, description="Progress percentage of the task")
    life_area_id: Optional[int] = Field(None, description="Associated life area ID")
    dependencies: Optional[List[int]] = Field(default_factory=list, description="Prerequisite task IDs")

class TaskCreate(TaskBase):
    goal_id: int = Field(..., description="Parent goal ID")

class Task(TaskBase):
    id: int = Field(..., description="Unique task ID")
    goal_id: int = Field(..., description="Associated goal ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        orm_mode = True

class LifeAreaBase(BaseModel):
    name: str = Field(..., description="Name of the life area", min_length=1, max_length=100)
    weight: Optional[int] = Field(10, description="Importance weight as percentage (0-100)", ge=0, le=100)
    icon: Optional[str] = Field(None, description="UI icon identifier", max_length=50)
    color: Optional[str] = Field(None, description="UI color preference (hex or color name)", max_length=50)
    description: Optional[str] = Field(None, description="Description of this life area", max_length=500)

class LifeAreaCreate(LifeAreaBase):
    """Schema for creating a new LifeArea"""
    pass

class LifeAreaUpdate(BaseModel):
    """Schema for updating a LifeArea (all fields optional)"""
    name: Optional[str] = Field(None, description="Name of the life area", min_length=1, max_length=100)
    weight: Optional[int] = Field(None, description="Importance weight as percentage (0-100)", ge=0, le=100)
    icon: Optional[str] = Field(None, description="UI icon identifier", max_length=50)
    color: Optional[str] = Field(None, description="UI color preference", max_length=50)
    description: Optional[str] = Field(None, description="Description of this life area", max_length=500)

class LifeArea(LifeAreaBase):
    id: int = Field(..., description="Unique life area ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        orm_mode = True

class MediaAttachmentBase(BaseModel):
    filename: str = Field(..., description="System filename for the attachment", min_length=1)
    original_filename: str = Field(..., description="Original filename from upload", min_length=1)
    file_path: str = Field(..., description="Full path to the stored file", min_length=1)
    file_size: int = Field(..., description="File size in bytes", ge=0)
    mime_type: str = Field(..., description="MIME type (e.g., image/jpeg, video/mp4)", min_length=1)
    file_type: str = Field(..., description="File category: image, video, audio, document", min_length=1)
    title: Optional[str] = Field(None, description="User-defined title for the attachment", max_length=200)
    description: Optional[str] = Field(None, description="User description for storytelling", max_length=1000)
    duration: Optional[int] = Field(None, description="Duration in seconds for video/audio", ge=0)
    width: Optional[int] = Field(None, description="Width in pixels for images/videos", ge=0)
    height: Optional[int] = Field(None, description="Height in pixels for images/videos", ge=0)

class MediaAttachmentCreate(MediaAttachmentBase):
    """Schema for creating a new MediaAttachment"""
    goal_id: Optional[int] = Field(None, description="ID of associated goal")
    task_id: Optional[int] = Field(None, description="ID of associated task")

class MediaAttachmentUpdate(BaseModel):
    """Schema for updating a MediaAttachment (metadata only)"""
    title: Optional[str] = Field(None, description="User-defined title for the attachment", max_length=200)
    description: Optional[str] = Field(None, description="User description for storytelling", max_length=1000)
    goal_id: Optional[int] = Field(None, description="ID of associated goal")  
    task_id: Optional[int] = Field(None, description="ID of associated task")

class MediaAttachment(MediaAttachmentBase):
    id: int = Field(..., description="Unique media attachment ID")
    user_id: str = Field(..., description="Owner user ID")
    goal_id: Optional[int] = Field(None, description="Associated goal ID")
    task_id: Optional[int] = Field(None, description="Associated task ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        orm_mode = True

class MemoryItem(BaseModel):
    id: int = Field(..., description="Unique memory item ID")
    user_id: str = Field(..., description="Owner user ID")
    content: str = Field(..., description="Content of the memory item")
    timestamp: datetime = Field(..., description="When the memory was recorded")

    class Config:
        orm_mode = True

## UserPreferences Schemas
class UserPreferencesBase(BaseModel):
    # Tone and communication preferences
    tone: Optional[Literal["friendly", "coach", "minimal", "professional"]] = Field("friendly", description="Communication tone preference")
    
    # Notification preferences
    notification_time: Optional[time] = Field(None, description="Preferred time for daily notifications (HH:MM)")
    notifications_enabled: Optional[bool] = Field(True, description="Enable/disable notifications")
    email_notifications: Optional[bool] = Field(False, description="Enable/disable email notifications")
    
    # Content and visualization preferences
    prefers_video: Optional[bool] = Field(True, description="Prefers video content")
    prefers_audio: Optional[bool] = Field(False, description="Prefers audio content")
    default_view: Optional[Literal["list", "card", "timeline"]] = Field("card", description="Default view mode")
    
    # Feature preferences
    mood_tracking_enabled: Optional[bool] = Field(False, description="Enable mood tracking feature")
    progress_charts_enabled: Optional[bool] = Field(True, description="Enable progress charts")
    ai_suggestions_enabled: Optional[bool] = Field(True, description="Enable AI suggestions")
    
    # Default associations
    default_life_area_id: Optional[int] = Field(None, description="Default life area ID for new goals/tasks")
    
    # Privacy and data preferences
    data_sharing_enabled: Optional[bool] = Field(False, description="Allow data sharing for improvements")
    analytics_enabled: Optional[bool] = Field(True, description="Enable analytics tracking")

class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences"""
    pass

class UserPreferencesUpdate(UserPreferencesBase):
    """Schema for updating user preferences - all fields optional"""
    pass

class UserPreferences(UserPreferencesBase):
    id: str = Field(..., description="Unique preferences ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        orm_mode = True

## FeedbackLog Schemas
class FeedbackLogBase(BaseModel):
    # Context information
    context_type: str = Field(..., description="Type of context (task, goal, plan, suggestion, ui_interaction, etc.)")
    context_id: Optional[str] = Field(None, description="ID of the related entity (goal_id, task_id, etc.)")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data (query, response, etc.)")
    
    # Feedback details
    feedback_type: Literal["positive", "negative", "neutral"] = Field(..., description="Type of feedback")
    feedback_value: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Numeric feedback score (-1.0 to 1.0)")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional user comment")
    
    # ML/RLHF specific fields
    action_taken: Optional[Dict[str, Any]] = Field(None, description="What action was taken (for RL)")
    reward_signal: Optional[float] = Field(None, description="Computed reward signal")
    model_version: Optional[str] = Field(None, description="Version of model that generated the response")
    
    # Metadata
    session_id: Optional[str] = Field(None, description="Session identifier for grouping related feedback")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device/platform information")
    feature_flags: Optional[Dict[str, Any]] = Field(None, description="Active feature flags during interaction")

class FeedbackLogCreate(FeedbackLogBase):
    """Schema for creating feedback logs"""
    pass

class FeedbackLogUpdate(BaseModel):
    """Schema for updating feedback logs - limited fields"""
    comment: Optional[str] = Field(None, max_length=1000, description="Updated user comment")
    processed_at: Optional[datetime] = Field(None, description="When feedback was processed for training")

class FeedbackLog(FeedbackLogBase):
    id: str = Field(..., description="Unique feedback log ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="When feedback was processed for training")

    class Config:
        orm_mode = True

class FeedbackLogSummary(BaseModel):
    """Summary statistics for feedback logs"""
    total_feedback: int = Field(..., description="Total number of feedback entries")
    positive_count: int = Field(..., description="Number of positive feedback entries")
    negative_count: int = Field(..., description="Number of negative feedback entries")
    neutral_count: int = Field(..., description="Number of neutral feedback entries")
    average_score: Optional[float] = Field(None, description="Average feedback score")
    context_breakdown: Dict[str, int] = Field(..., description="Breakdown by context type")
    recent_feedback: List[FeedbackLog] = Field(..., description="Most recent feedback entries")