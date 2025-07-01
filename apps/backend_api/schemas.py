from pydantic import BaseModel, Field, validator, root_validator, EmailStr, constr
from typing import Optional, List, Literal, Dict, Any, TYPE_CHECKING
from datetime import datetime, time
import re

# Forward references for nested schemas
if TYPE_CHECKING:
    from typing import ForwardRef
    MediaAttachmentOut = ForwardRef('MediaAttachmentOut')
    UserPreferencesOut = ForwardRef('UserPreferencesOut')
    LifeAreaOut = ForwardRef('LifeAreaOut')

## Authentication Schemas
class RegisterRequest(BaseModel):
    username: Optional[str] = Field(None, description="Username or email address")
    password: Optional[str] = Field(None, description="Password")
    
    # Social login fields
    provider: Optional[Literal["email", "google", "apple", "facebook"]] = Field("email", description="Authentication provider")
    social_token: Optional[str] = Field(None, description="OAuth token from social provider")
    email: Optional[str] = Field(None, description="Email from social provider")
    display_name: Optional[str] = Field(None, description="Display name from social provider")
    
    @root_validator(skip_on_failure=True)
    def validate_fields_by_provider(cls, values):
        provider = values.get('provider', 'email')
        if provider == 'email':
            username = values.get('username')
            password = values.get('password')
            
            if not username or username.isspace():
                raise ValueError('Username is required for email registration')
            if not password or password.isspace():
                raise ValueError('Password is required for email registration')
                
            # Username validation
            username = username.strip()
            if len(username) < 3 or len(username) > 50:
                raise ValueError('Username must be 3-50 characters')
                
            # Allow both usernames and email addresses
            if '@' in username:
                # Basic email validation
                if not username.count('@') == 1 or not '.' in username.split('@')[1]:
                    raise ValueError('Invalid email format')
            else:
                # Username validation - no consecutive special chars
                if '..' in username or '__' in username:
                    raise ValueError('Username cannot contain consecutive dots or underscores')
                    
            # Password validation
            if len(password) < 8 or len(password) > 128:
                raise ValueError('Password must be 8-128 characters')
            if not re.search(r'[A-Za-z]', password):
                raise ValueError('Password must contain at least one letter')
            if not re.search(r'[0-9]', password):
                raise ValueError('Password must contain at least one number')
                
            values['username'] = username.lower()
        else:
            if not values.get('social_token'):
                raise ValueError('Social token is required for social registration')
            if not values.get('email'):
                raise ValueError('Email is required for social registration')
        return values

class LoginRequest(BaseModel):
    username: Optional[str] = Field(None, description="Username or email")
    password: Optional[str] = Field(None, description="Password")
    
    # Social login fields
    provider: Optional[Literal["email", "google", "apple", "facebook"]] = Field("email", description="Authentication provider")
    social_token: Optional[str] = Field(None, description="OAuth token from social provider")
    email: Optional[str] = Field(None, description="Email from social provider")
    
    @root_validator(skip_on_failure=True)
    def validate_fields_by_provider(cls, values):
        provider = values.get('provider', 'email')
        if provider == 'email':
            username = values.get('username')
            password = values.get('password')
            
            if not username or username.isspace():
                raise ValueError('Username is required for email login')
            if not password:
                raise ValueError('Password is required for email login')
                
            # Additional username validation for email login
            username = username.strip()
            if '@' in username:
                # Basic email validation
                if not username.count('@') == 1 or not '.' in username.split('@')[1]:
                    raise ValueError('Invalid email format')
            
            values['username'] = username.lower()
        else:
            if not values.get('social_token'):
                raise ValueError('Social token is required for social login')
            if not values.get('email'):
                raise ValueError('Email is required for social login')
        return values

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class User(BaseModel):
    uid: str = Field(..., description="Firebase user ID")
    email: str = Field(..., description="User email address")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    username: str = Field(..., description="Unique username")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    
    # Optional preferences to set during registration
    preferences: Optional['UserPreferencesCreate'] = Field(None, description="Initial user preferences")

class GoalBase(BaseModel):
    title: constr(min_length=1, max_length=200, strip_whitespace=True) = Field(
        ..., 
        description="Title of the goal (1-200 characters)"
    )
    description: Optional[constr(max_length=2000, strip_whitespace=True)] = Field(
        None, 
        description="Detailed description of the goal (max 2000 characters)"
    )
    status: Optional[Literal['todo', 'in_progress', 'completed', 'paused']] = Field(
        'todo', 
        description="Status of the goal"
    )
    progress: Optional[float] = Field(
        0.0, 
        ge=0.0, 
        le=100.0, 
        description="Progress percentage (0-100)"
    )
    life_area_id: Optional[int] = Field(
        None, 
        gt=0, 
        description="Associated life area ID (positive integer)"
    )
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Goal title cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

class GoalCreate(GoalBase):
    """Schema for creating a new Goal"""
    project_id: Optional[int] = Field(None, gt=0, description="Associated project ID (positive integer)")

class Goal(GoalBase):
    id: int = Field(..., description="Unique goal ID")
    user_id: str = Field(..., description="Owner user ID")
    project_id: Optional[int] = Field(None, description="Associated project ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    title: constr(min_length=1, max_length=200, strip_whitespace=True) = Field(
        ..., 
        description="Title of the project (1-200 characters)"
    )
    description: Optional[constr(max_length=2000, strip_whitespace=True)] = Field(
        None, 
        description="Detailed description of the project (max 2000 characters)"
    )
    status: Optional[Literal['todo', 'in_progress', 'completed', 'paused']] = Field(
        'todo', 
        description="Status of the project"
    )
    progress: Optional[float] = Field(
        0.0, 
        ge=0.0, 
        le=100.0, 
        description="Progress percentage (0-100)"
    )
    life_area_id: Optional[int] = Field(
        None, 
        gt=0, 
        description="Associated life area ID (positive integer)"
    )
    start_date: Optional[datetime] = Field(None, description="Optional start date for the project")
    target_date: Optional[datetime] = Field(None, description="Optional target completion date")
    priority: Optional[Literal['low', 'medium', 'high']] = Field(
        'medium', 
        description="Priority level of the project"
    )
    phases: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, 
        description="Project phases/milestones",
        max_items=20
    )
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Project title cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v
    
    @validator('start_date')
    def validate_start_date(cls, v):
        if v is not None:
            # Don't allow start dates more than 10 years in the future
            from datetime import datetime, timedelta
            max_future = datetime.utcnow() + timedelta(days=3650)
            if v > max_future:
                raise ValueError('Start date cannot be more than 10 years in the future')
        return v
    
    @validator('target_date')
    def validate_target_date(cls, v, values):
        if v is not None:
            # Don't allow target dates more than 10 years in the future
            from datetime import datetime, timedelta
            max_future = datetime.utcnow() + timedelta(days=3650)
            if v > max_future:
                raise ValueError('Target date cannot be more than 10 years in the future')
            
            # Target date should be after start date if both are provided
            if 'start_date' in values and values['start_date'] is not None:
                if v < values['start_date']:
                    raise ValueError('Target date must be after start date')
        return v

class ProjectCreate(ProjectBase):
    """Schema for creating a new Project"""
    pass

class Project(ProjectBase):
    id: int = Field(..., description="Unique project ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: constr(min_length=1, max_length=200, strip_whitespace=True) = Field(
        ..., 
        description="Title of the task (1-200 characters)"
    )
    description: Optional[constr(max_length=2000, strip_whitespace=True)] = Field(
        None, 
        description="Detailed description of the task (max 2000 characters)"
    )
    due_date: Optional[datetime] = Field(None, description="Optional due date for the task")
    duration: Optional[int] = Field(
        None, 
        gt=0, 
        le=1440, 
        description="Expected duration in minutes (1-1440, max 24 hours)"
    )
    status: Optional[Literal['todo', 'in_progress', 'completed', 'cancelled']] = Field(
        'todo', 
        description="Status of the task"
    )
    progress: Optional[float] = Field(
        0.0, 
        ge=0.0, 
        le=100.0, 
        description="Progress percentage (0-100)"
    )
    life_area_id: Optional[int] = Field(
        None, 
        gt=0, 
        description="Associated life area ID (positive integer)"
    )
    dependencies: Optional[List[int]] = Field(
        default_factory=list, 
        description="Prerequisite task IDs (max 10 dependencies)",
        max_items=10
    )
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Task title cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v):
        if v is not None:
            # Don't allow due dates more than 10 years in the future
            from datetime import datetime, timedelta
            max_future = datetime.utcnow() + timedelta(days=3650)
            if v > max_future:
                raise ValueError('Due date cannot be more than 10 years in the future')
        return v
    
    @validator('dependencies')
    def validate_dependencies(cls, v):
        if v is not None:
            # Remove duplicates and ensure all are positive integers
            unique_deps = list(set([dep for dep in v if isinstance(dep, int) and dep > 0]))
            return unique_deps
        return []

class TaskCreate(TaskBase):
    goal_id: Optional[int] = Field(None, description="Parent goal ID")
    project_id: Optional[int] = Field(None, description="Parent project ID")
    
    @root_validator(skip_on_failure=True)
    def validate_parent_reference(cls, values):
        goal_id = values.get('goal_id')
        project_id = values.get('project_id')
        
        # At least one parent (goal or project) must be specified
        if not goal_id and not project_id:
            raise ValueError('Either goal_id or project_id must be specified')
        
        return values

class Task(TaskBase):
    id: int = Field(..., description="Unique task ID")
    goal_id: Optional[int] = Field(None, description="Associated goal ID")
    project_id: Optional[int] = Field(None, description="Associated project ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class LifeAreaBase(BaseModel):
    name: constr(min_length=1, max_length=100, strip_whitespace=True) = Field(
        ..., 
        description="Name of the life area (1-100 characters)"
    )
    weight: Optional[int] = Field(
        10, 
        ge=0, 
        le=100, 
        description="Importance weight as percentage (0-100)"
    )
    icon: Optional[constr(max_length=50, strip_whitespace=True)] = Field(
        None, 
        description="UI icon identifier (max 50 characters)"
    )
    color: Optional[constr(max_length=50, strip_whitespace=True)] = Field(
        None, 
        description="UI color preference (hex or color name, max 50 characters)"
    )
    description: Optional[constr(max_length=500, strip_whitespace=True)] = Field(
        None, 
        description="Description of this life area (max 500 characters)"
    )
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Life area name cannot be empty')
        return v.strip()
    
    @validator('color')
    def validate_color(cls, v):
        if v is not None:
            v = v.strip()
            # Basic hex color validation
            if v.startswith('#') and len(v) in [4, 7]:
                if not all(c in '0123456789ABCDEFabcdef' for c in v[1:]):
                    raise ValueError('Invalid hex color format')
            return v
        return v

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
        from_attributes = True

class MediaAttachmentBase(BaseModel):
    filename: constr(min_length=1, max_length=255, strip_whitespace=True) = Field(
        ..., 
        description="System filename for the attachment (1-255 characters)"
    )
    original_filename: constr(min_length=1, max_length=255, strip_whitespace=True) = Field(
        ..., 
        description="Original filename from upload (1-255 characters)"
    )
    file_path: constr(min_length=1, max_length=1000, strip_whitespace=True) = Field(
        ..., 
        description="Full path to the stored file (1-1000 characters)"
    )
    file_size: int = Field(
        ..., 
        ge=0, 
        le=1073741824,  # 1GB max
        description="File size in bytes (max 1GB)"
    )
    mime_type: constr(min_length=1, max_length=100, strip_whitespace=True) = Field(
        ..., 
        description="MIME type (e.g., image/jpeg, video/mp4)"
    )
    file_type: Literal["image", "video", "audio", "document"] = Field(
        ..., 
        description="File category: image, video, audio, document"
    )
    title: Optional[constr(max_length=200, strip_whitespace=True)] = Field(
        None, 
        description="User-defined title for the attachment (max 200 characters)"
    )
    description: Optional[constr(max_length=1000, strip_whitespace=True)] = Field(
        None, 
        description="User description for storytelling (max 1000 characters)"
    )
    duration: Optional[int] = Field(
        None, 
        ge=0, 
        le=86400,  # 24 hours max
        description="Duration in seconds for video/audio (max 24 hours)"
    )
    width: Optional[int] = Field(
        None, 
        ge=1, 
        le=8192,  # 8K resolution max
        description="Width in pixels for images/videos (1-8192px)"
    )
    height: Optional[int] = Field(
        None, 
        ge=1, 
        le=8192,  # 8K resolution max
        description="Height in pixels for images/videos (1-8192px)"
    )
    
    @validator('mime_type')
    def validate_mime_type(cls, v):
        allowed_mime_types = {
            'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
            'video': ['video/mp4', 'video/webm', 'video/avi', 'video/mov', 'video/wmv'],
            'audio': ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac', 'audio/flac'],
            'document': ['application/pdf', 'text/plain', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        }
        
        # Check if mime type is in any allowed category
        for category, mime_types in allowed_mime_types.items():
            if v in mime_types:
                return v
        
        # If not in predefined list, allow but warn
        if '/' not in v:
            raise ValueError('Invalid MIME type format')
        return v
    
    @validator('file_type')
    def validate_file_type_consistency(cls, v, values):
        if 'mime_type' in values:
            mime_type = values['mime_type']
            if v == 'image' and not mime_type.startswith('image/'):
                raise ValueError('File type and MIME type mismatch')
            elif v == 'video' and not mime_type.startswith('video/'):
                raise ValueError('File type and MIME type mismatch')
            elif v == 'audio' and not mime_type.startswith('audio/'):
                raise ValueError('File type and MIME type mismatch')
        return v

class MediaAttachmentCreate(MediaAttachmentBase):
    """Schema for creating a new MediaAttachment"""
    goal_id: Optional[int] = Field(None, description="ID of associated goal")
    project_id: Optional[int] = Field(None, description="ID of associated project")
    task_id: Optional[int] = Field(None, description="ID of associated task")

class MediaAttachmentUpdate(BaseModel):
    """Schema for updating a MediaAttachment (metadata only)"""
    title: Optional[str] = Field(None, description="User-defined title for the attachment", max_length=200)
    description: Optional[str] = Field(None, description="User description for storytelling", max_length=1000)
    goal_id: Optional[int] = Field(None, description="ID of associated goal")
    project_id: Optional[int] = Field(None, description="ID of associated project")
    task_id: Optional[int] = Field(None, description="ID of associated task")

class MediaAttachment(MediaAttachmentBase):
    id: int = Field(..., description="Unique media attachment ID")
    user_id: str = Field(..., description="Owner user ID")
    goal_id: Optional[int] = Field(None, description="Associated goal ID")
    project_id: Optional[int] = Field(None, description="Associated project ID")
    task_id: Optional[int] = Field(None, description="Associated task ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True

class MemoryItem(BaseModel):
    id: int = Field(..., description="Unique memory item ID")
    user_id: str = Field(..., description="Owner user ID")
    content: str = Field(..., description="Content of the memory item")
    timestamp: datetime = Field(..., description="When the memory was recorded")

    class Config:
        from_attributes = True

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
        from_attributes = True

# Enhanced Output Schemas with Nested Relationships

class MediaAttachmentOut(MediaAttachment):
    """Enhanced media attachment output schema"""
    pass

class LifeAreaOut(LifeArea):
    """Enhanced life area output schema"""
    pass

class ProjectOut(Project):
    """Enhanced project output schema with nested relationships"""
    goals: List['Goal'] = Field(default_factory=list, description="Associated goals")
    tasks: List['Task'] = Field(default_factory=list, description="Associated tasks")
    media: List['MediaAttachmentOut'] = Field(default_factory=list, description="Associated media attachments")
    life_area: Optional['LifeAreaOut'] = Field(None, description="Associated life area details")

class TaskOut(Task):
    """Enhanced task output schema with nested relationships"""
    media: List['MediaAttachmentOut'] = Field(default_factory=list, description="Associated media attachments")
    life_area: Optional['LifeAreaOut'] = Field(None, description="Associated life area details")
    project: Optional['ProjectOut'] = Field(None, description="Associated project details")

class GoalOut(Goal):
    """Enhanced goal output schema with nested relationships"""
    tasks: List['TaskOut'] = Field(default_factory=list, description="Associated tasks")
    media: List['MediaAttachmentOut'] = Field(default_factory=list, description="Associated media attachments")
    life_area: Optional['LifeAreaOut'] = Field(None, description="Associated life area details")
    project: Optional['ProjectOut'] = Field(None, description="Associated project details")

class UserPreferencesOut(UserPreferences):
    """Enhanced user preferences output schema"""
    default_life_area: Optional['LifeAreaOut'] = Field(None, description="Default life area details")

class UserOut(User):
    """Enhanced user output schema with nested relationships"""
    preferences: Optional['UserPreferencesOut'] = Field(None, description="User preferences")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    
    class Config:
        from_attributes = True

## FeedbackLog Schemas
class FeedbackLogBase(BaseModel):
    # Context information
    context_type: constr(min_length=1, max_length=50, strip_whitespace=True) = Field(
        ..., 
        description="Type of context (task, goal, plan, suggestion, ui_interaction, etc.)"
    )
    context_id: Optional[constr(max_length=100, strip_whitespace=True)] = Field(
        None, 
        description="ID of the related entity (goal_id, task_id, etc.)"
    )
    context_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional context data (query, response, etc.)"
    )
    
    # Feedback details
    feedback_type: Literal["positive", "negative", "neutral"] = Field(
        ..., 
        description="Type of feedback"
    )
    feedback_value: Optional[float] = Field(
        None, 
        ge=-1.0, 
        le=1.0, 
        description="Numeric feedback score (-1.0 to 1.0)"
    )
    comment: Optional[constr(max_length=1000, strip_whitespace=True)] = Field(
        None, 
        description="Optional user comment (max 1000 characters)"
    )
    
    # ML/RLHF specific fields
    action_taken: Optional[Dict[str, Any]] = Field(
        None, 
        description="What action was taken (for RL)"
    )
    reward_signal: Optional[float] = Field(
        None, 
        ge=-10.0,
        le=10.0,
        description="Computed reward signal (-10.0 to 10.0)"
    )
    model_version: Optional[constr(max_length=50, strip_whitespace=True)] = Field(
        None, 
        description="Version of model that generated the response"
    )
    
    # Metadata
    session_id: Optional[constr(max_length=100, strip_whitespace=True)] = Field(
        None, 
        description="Session identifier for grouping related feedback"
    )
    device_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="Device/platform information"
    )
    feature_flags: Optional[Dict[str, Any]] = Field(
        None, 
        description="Active feature flags during interaction"
    )
    
    @validator('context_data')
    def validate_context_data(cls, v):
        if v is not None:
            # Limit context data size to prevent abuse
            if len(str(v)) > 10000:  # 10KB limit
                raise ValueError('Context data too large (max 10KB)')
        return v
    
    @validator('device_info')
    def validate_device_info(cls, v):
        if v is not None:
            # Ensure device info doesn't contain sensitive data
            sensitive_keys = ['password', 'token', 'key', 'secret']
            for key in v.keys():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    raise ValueError('Device info cannot contain sensitive data')
        return v

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
        from_attributes = True

class FeedbackLogSummary(BaseModel):
    """Summary statistics for feedback logs"""
    total_feedback: int = Field(..., description="Total number of feedback entries")
    positive_count: int = Field(..., description="Number of positive feedback entries")
    negative_count: int = Field(..., description="Number of negative feedback entries")
    neutral_count: int = Field(..., description="Number of neutral feedback entries")
    average_score: Optional[float] = Field(None, description="Average feedback score")
    context_breakdown: Dict[str, int] = Field(..., description="Breakdown by context type")
    recent_feedback: List[FeedbackLog] = Field(..., description="Most recent feedback entries")

## StorySession Schemas
class StorySessionBase(BaseModel):
    # Content information
    title: Optional[str] = Field(None, max_length=200, description="User-defined title for the story session")
    generated_text: Optional[str] = Field(None, description="AI-generated narrative text")
    video_url: Optional[str] = Field(None, description="URL to generated video")
    audio_url: Optional[str] = Field(None, description="URL to generated audio/narration")
    thumbnail_url: Optional[str] = Field(None, description="URL to video thumbnail")
    
    # Generation parameters
    summary_period: Optional[str] = Field(None, description="Period type: weekly, monthly, project-based, custom")
    period_start: Optional[datetime] = Field(None, description="Start of the period being summarized")
    period_end: Optional[datetime] = Field(None, description="End of the period being summarized")
    content_type: Optional[Literal["summary", "story", "reflection", "achievement"]] = Field("summary", description="Type of content generated")
    
    # Social media and distribution
    posted_to: Optional[List[str]] = Field(default_factory=list, description="Platforms where content was posted")
    posting_status: Optional[Literal["draft", "scheduled", "posted", "failed"]] = Field("draft", description="Current posting status")
    scheduled_post_time: Optional[datetime] = Field(None, description="When content is scheduled to be posted")
    
    # Generation metadata
    generation_prompt: Optional[str] = Field(None, description="The prompt used for generation")
    model_version: Optional[str] = Field(None, description="AI model version used")
    generation_params: Optional[Dict[str, Any]] = Field(None, description="Parameters used for generation")
    word_count: Optional[int] = Field(None, ge=0, description="Word count of generated text")
    estimated_read_time: Optional[int] = Field(None, ge=0, description="Estimated reading time in seconds")
    
    # Related content
    source_goals: Optional[List[int]] = Field(default_factory=list, description="Goal IDs that contributed to this story")
    source_tasks: Optional[List[int]] = Field(default_factory=list, description="Task IDs that contributed to this story")
    source_life_areas: Optional[List[int]] = Field(default_factory=list, description="Life area IDs featured in this story")
    
    # Engagement and analytics
    view_count: Optional[int] = Field(0, ge=0, description="Number of times viewed")
    like_count: Optional[int] = Field(0, ge=0, description="Number of likes")
    share_count: Optional[int] = Field(0, ge=0, description="Number of shares")
    engagement_data: Optional[Dict[str, Any]] = Field(None, description="Additional engagement metrics")
    
    # Quality and user feedback
    user_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="User rating 1-5 stars")
    user_notes: Optional[str] = Field(None, max_length=1000, description="User notes about the story")
    regeneration_count: Optional[int] = Field(0, ge=0, description="How many times this was regenerated")
    
    # Processing status
    processing_status: Optional[Literal["pending", "generating", "completed", "failed"]] = Field("pending", description="Current processing status")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")

class StorySessionCreate(StorySessionBase):
    """Schema for creating story sessions"""
    pass

class StorySessionUpdate(BaseModel):
    """Schema for updating story sessions - all fields optional"""
    title: Optional[str] = Field(None, max_length=200, description="User-defined title for the story session")
    generated_text: Optional[str] = Field(None, description="AI-generated narrative text")
    video_url: Optional[str] = Field(None, description="URL to generated video")
    audio_url: Optional[str] = Field(None, description="URL to generated audio/narration")
    thumbnail_url: Optional[str] = Field(None, description="URL to video thumbnail")
    summary_period: Optional[str] = Field(None, description="Period type: weekly, monthly, project-based, custom")
    period_start: Optional[datetime] = Field(None, description="Start of the period being summarized")
    period_end: Optional[datetime] = Field(None, description="End of the period being summarized")
    content_type: Optional[Literal["summary", "story", "reflection", "achievement"]] = Field(None, description="Type of content generated")
    posted_to: Optional[List[str]] = Field(None, description="Platforms where content was posted")
    posting_status: Optional[Literal["draft", "scheduled", "posted", "failed"]] = Field(None, description="Current posting status")
    scheduled_post_time: Optional[datetime] = Field(None, description="When content is scheduled to be posted")
    generation_prompt: Optional[str] = Field(None, description="The prompt used for generation")
    model_version: Optional[str] = Field(None, description="AI model version used")
    generation_params: Optional[Dict[str, Any]] = Field(None, description="Parameters used for generation")
    word_count: Optional[int] = Field(None, ge=0, description="Word count of generated text")
    estimated_read_time: Optional[int] = Field(None, ge=0, description="Estimated reading time in seconds")
    source_goals: Optional[List[int]] = Field(None, description="Goal IDs that contributed to this story")
    source_tasks: Optional[List[int]] = Field(None, description="Task IDs that contributed to this story")
    source_life_areas: Optional[List[int]] = Field(None, description="Life area IDs featured in this story")
    view_count: Optional[int] = Field(None, ge=0, description="Number of times viewed")
    like_count: Optional[int] = Field(None, ge=0, description="Number of likes")
    share_count: Optional[int] = Field(None, ge=0, description="Number of shares")
    engagement_data: Optional[Dict[str, Any]] = Field(None, description="Additional engagement metrics")
    user_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="User rating 1-5 stars")
    user_notes: Optional[str] = Field(None, max_length=1000, description="User notes about the story")
    regeneration_count: Optional[int] = Field(None, ge=0, description="How many times this was regenerated")
    processing_status: Optional[Literal["pending", "generating", "completed", "failed"]] = Field(None, description="Current processing status")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    generated_at: Optional[datetime] = Field(None, description="When generation was completed")
    posted_at: Optional[datetime] = Field(None, description="When content was actually posted")

class StorySession(StorySessionBase):
    id: str = Field(..., description="Unique story session ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    generated_at: Optional[datetime] = Field(None, description="When generation was completed")
    posted_at: Optional[datetime] = Field(None, description="When content was actually posted")

    class Config:
        from_attributes = True

class StorySessionSummary(BaseModel):
    """Summary statistics for story sessions"""
    total_sessions: int = Field(..., description="Total number of story sessions")
    by_content_type: Dict[str, int] = Field(..., description="Breakdown by content type")
    by_posting_status: Dict[str, int] = Field(..., description="Breakdown by posting status")
    by_processing_status: Dict[str, int] = Field(..., description="Breakdown by processing status")
    total_word_count: int = Field(..., description="Total words generated")
    average_rating: Optional[float] = Field(None, description="Average user rating")
    recent_sessions: List[StorySession] = Field(..., description="Most recent story sessions")

class GenerationRequest(BaseModel):
    """Schema for requesting story generation"""
    title: Optional[str] = Field(None, max_length=200, description="Title for the story session")
    summary_period: str = Field(..., description="Period type: weekly, monthly, project-based, custom")
    period_start: Optional[datetime] = Field(None, description="Start of the period to summarize")
    period_end: Optional[datetime] = Field(None, description="End of the period to summarize")
    content_type: Literal["summary", "story", "reflection", "achievement"] = Field("summary", description="Type of content to generate")
    generation_prompt: Optional[str] = Field(None, description="Custom prompt for generation")
    include_goals: bool = Field(True, description="Include goals in the generation")
    include_tasks: bool = Field(True, description="Include tasks in the generation")
    include_life_areas: Optional[List[int]] = Field(None, description="Specific life areas to focus on")
    generation_params: Optional[Dict[str, Any]] = Field(None, description="Custom generation parameters")

class PublishRequest(BaseModel):
    """Schema for publishing story content"""
    platforms: List[str] = Field(..., min_items=1, description="Platforms to publish to")
    scheduled_time: Optional[datetime] = Field(None, description="When to schedule the post")
    custom_message: Optional[str] = Field(None, max_length=500, description="Custom message for the post")