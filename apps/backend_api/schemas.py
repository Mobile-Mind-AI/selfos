import re
from datetime import datetime, time
from typing import TYPE_CHECKING, Any, Literal, Optional

from pydantic import (
    BaseModel,
    Field,
    constr,
    root_validator,
    validator,
)

# Forward references for nested schemas
if TYPE_CHECKING:
    from typing import ForwardRef

    MediaAttachmentOut = ForwardRef("MediaAttachmentOut")
    UserPreferencesOut = ForwardRef("UserPreferencesOut")
    LifeAreaOut = ForwardRef("LifeAreaOut")


## Authentication Schemas
class RegisterRequest(BaseModel):
    username: str | None = Field(None, description="Username or email address")
    password: str | None = Field(None, description="Password")

    # Social login fields
    provider: Literal["email", "google", "apple", "facebook"] | None = Field(
        "email", description="Authentication provider"
    )
    social_token: str | None = Field(
        None, description="OAuth token from social provider"
    )
    email: str | None = Field(None, description="Email from social provider")
    display_name: str | None = Field(
        None, description="Display name from social provider"
    )

    @root_validator(skip_on_failure=True)
    def validate_fields_by_provider(cls, values):
        provider = values.get("provider", "email")
        if provider == "email":
            username = values.get("username")
            password = values.get("password")

            if not username or username.isspace():
                raise ValueError("Username is required for email registration")
            if not password or password.isspace():
                raise ValueError("Password is required for email registration")

            # Username validation
            username = username.strip()
            if len(username) < 3 or len(username) > 50:
                raise ValueError("Username must be 3-50 characters")

            # Allow both usernames and email addresses
            if "@" in username:
                # Basic email validation
                if not username.count("@") == 1 or "." not in username.split("@")[1]:
                    raise ValueError("Invalid email format")
            else:
                # Username validation - no consecutive special chars
                if ".." in username or "__" in username:
                    raise ValueError(
                        "Username cannot contain consecutive dots or underscores"
                    )

            # Password validation
            if len(password) < 8 or len(password) > 128:
                raise ValueError("Password must be 8-128 characters")
            if not re.search(r"[A-Za-z]", password):
                raise ValueError("Password must contain at least one letter")
            if not re.search(r"[0-9]", password):
                raise ValueError("Password must contain at least one number")

            values["username"] = username.lower()
        else:
            if not values.get("social_token"):
                raise ValueError("Social token is required for social registration")
            if not values.get("email"):
                raise ValueError("Email is required for social registration")
        return values


class LoginRequest(BaseModel):
    username: str | None = Field(None, description="Username or email")
    password: str | None = Field(None, description="Password")

    # Social login fields
    provider: Literal["email", "google", "apple", "facebook"] | None = Field(
        "email", description="Authentication provider"
    )
    social_token: str | None = Field(
        None, description="OAuth token from social provider"
    )
    email: str | None = Field(None, description="Email from social provider")

    @root_validator(skip_on_failure=True)
    def validate_fields_by_provider(cls, values):
        provider = values.get("provider", "email")
        if provider == "email":
            username = values.get("username")
            password = values.get("password")

            if not username or username.isspace():
                raise ValueError("Username is required for email login")
            if not password:
                raise ValueError("Password is required for email login")

            # Additional username validation for email login
            username = username.strip()
            if "@" in username:
                # Basic email validation
                if not username.count("@") == 1 or "." not in username.split("@")[1]:
                    raise ValueError("Invalid email format")

            values["username"] = username.lower()
        else:
            if not values.get("social_token"):
                raise ValueError("Social token is required for social login")
            if not values.get("email"):
                raise ValueError("Email is required for social login")
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
    preferences: Optional["UserPreferencesCreate"] = Field(
        None, description="Initial user preferences"
    )


class GoalBase(BaseModel):
    title: constr(min_length=1, max_length=200, strip_whitespace=True) = Field(
        ..., description="Title of the goal (1-200 characters)"
    )
    description: constr(max_length=2000, strip_whitespace=True) | None = Field(
        None, description="Detailed description of the goal (max 2000 characters)"
    )
    status: Literal["todo", "in_progress", "completed", "paused"] | None = Field(
        "todo", description="Status of the goal"
    )
    progress: float | None = Field(
        0.0, ge=0.0, le=100.0, description="Progress percentage (0-100)"
    )
    life_area_id: int | None = Field(
        None, gt=0, description="Associated life area ID (positive integer)"
    )

    @validator("title")
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Goal title cannot be empty")
        return v.strip()

    @validator("description")
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class GoalCreate(GoalBase):
    """Schema for creating a new Goal"""

    project_id: int | None = Field(
        None, gt=0, description="Associated project ID (positive integer)"
    )
    parent_id: int | None = Field(
        None, gt=0, description="Parent goal ID for hierarchical organization"
    )
    tag_ids: list[int] | None = Field(
        default_factory=list, description="List of tag IDs to associate"
    )

    @validator("parent_id")
    def validate_parent_id(cls, v, values):
        # Cannot be parent of itself (will be validated in service layer)
        if v is not None and v <= 0:
            raise ValueError("Parent ID must be a positive integer")
        return v


class Goal(GoalBase):
    id: int = Field(..., description="Unique goal ID")
    user_id: str = Field(..., description="Owner user ID")
    project_id: int | None = Field(None, description="Associated project ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    title: constr(min_length=1, max_length=200, strip_whitespace=True) = Field(
        ..., description="Title of the project (1-200 characters)"
    )
    description: constr(max_length=2000, strip_whitespace=True) | None = Field(
        None, description="Detailed description of the project (max 2000 characters)"
    )
    status: Literal["planning", "active", "on_hold", "completed"] | None = Field(
        "planning", description="Status of the project"
    )
    progress: float | None = Field(
        0.0, ge=0.0, le=100.0, description="Progress percentage (0-100)"
    )
    life_area_id: int | None = Field(
        None, gt=0, description="Associated life area ID (positive integer)"
    )
    priority: Literal["low", "medium", "high"] | None = Field(
        "medium", description="Priority level of the project"
    )

    @validator("title")
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Project title cannot be empty")
        return v.strip()

    @validator("description")
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating a new Project"""

    parent_id: int | None = Field(
        None, gt=0, description="Parent project ID for hierarchical organization"
    )
    tag_ids: list[int] | None = Field(
        default_factory=list, description="List of tag IDs to associate"
    )

    @validator("parent_id")
    def validate_parent_id(cls, v, values):
        # Cannot be parent of itself (will be validated in service layer)
        if v is not None and v <= 0:
            raise ValueError("Parent ID must be a positive integer")
        return v


class Project(ProjectBase):
    id: int = Field(..., description="Unique project ID")
    user_id: str = Field(..., description="Owner user ID")
    parent_id: int | None = Field(
        None, description="Parent project ID for hierarchical organization"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: constr(min_length=1, max_length=200, strip_whitespace=True) = Field(
        ..., description="Title of the task (1-200 characters)"
    )
    description: constr(max_length=2000, strip_whitespace=True) | None = Field(
        None, description="Detailed description of the task (max 2000 characters)"
    )
    due_date: datetime | None = Field(
        None, description="Optional due date for the task"
    )
    estimated_hours: float | None = Field(
        None, gt=0, description="Estimated hours to complete the task"
    )
    actual_hours: float | None = Field(
        None, gt=0, description="Actual hours spent on the task"
    )
    status: Literal["todo", "in_progress", "completed", "cancelled"] | None = Field(
        "todo", description="Status of the task"
    )
    progress: float | None = Field(
        0.0, ge=0.0, le=100.0, description="Progress percentage (0-100)"
    )
    life_area_id: int | None = Field(
        None, gt=0, description="Associated life area ID (positive integer)"
    )
    dependencies: list[int] | None = Field(
        default_factory=list,
        description="Prerequisite task IDs (max 10 dependencies)",
        max_items=10,
    )

    @validator("title")
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Task title cannot be empty")
        return v.strip()

    @validator("description")
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @validator("due_date")
    def validate_due_date(cls, v):
        if v is not None:
            # Don't allow due dates more than 10 years in the future
            from datetime import datetime, timedelta

            max_future = datetime.utcnow() + timedelta(days=3650)
            if v > max_future:
                raise ValueError("Due date cannot be more than 10 years in the future")
        return v

    @validator("dependencies")
    def validate_dependencies(cls, v):
        if v is not None:
            # Remove duplicates and ensure all are positive integers
            unique_deps = list(
                {dep for dep in v if isinstance(dep, int) and dep > 0}
            )
            return unique_deps
        return []


class TaskCreate(TaskBase):
    goal_id: int | None = Field(None, description="Parent goal ID")
    project_id: int | None = Field(None, description="Parent project ID")
    parent_id: int | None = Field(
        None, gt=0, description="Parent task ID for hierarchical organization"
    )
    tag_ids: list[int] | None = Field(
        default_factory=list, description="List of tag IDs to associate"
    )

    @validator("parent_id")
    def validate_parent_id(cls, v, values):
        # Cannot be parent of itself (will be validated in service layer)
        if v is not None and v <= 0:
            raise ValueError("Parent ID must be a positive integer")
        return v

    @root_validator(skip_on_failure=True)
    def validate_parent_reference(cls, values):
        goal_id = values.get("goal_id")
        project_id = values.get("project_id")

        # At least one parent (goal or project) must be specified
        if not goal_id and not project_id:
            raise ValueError("Either goal_id or project_id must be specified")

        return values


class Task(TaskBase):
    id: int = Field(..., description="Unique task ID")
    goal_id: int | None = Field(None, description="Associated goal ID")
    project_id: int | None = Field(None, description="Associated project ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class LifeAreaBase(BaseModel):
    name: constr(min_length=1, max_length=100, strip_whitespace=True) = Field(
        ..., description="Name of the life area (1-100 characters)"
    )
    weight: int | None = Field(
        10, ge=0, le=100, description="Importance weight as percentage (0-100)"
    )
    icon: constr(max_length=50, strip_whitespace=True) | None = Field(
        None, description="UI icon identifier (max 50 characters)"
    )
    color: constr(max_length=50, strip_whitespace=True) | None = Field(
        None, description="UI color preference (hex or color name, max 50 characters)"
    )
    description: constr(max_length=500, strip_whitespace=True) | None = Field(
        None, description="Description of this life area (max 500 characters)"
    )

    @validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Life area name cannot be empty")
        return v.strip()

    @validator("color")
    def validate_color(cls, v):
        if v is not None:
            v = v.strip()
            # Basic hex color validation
            if v.startswith("#") and len(v) in [4, 7]:
                if not all(c in "0123456789ABCDEFabcdef" for c in v[1:]):
                    raise ValueError("Invalid hex color format")
            return v
        return v


class LifeAreaCreate(LifeAreaBase):
    """Schema for creating a new LifeArea"""

    pass


class LifeAreaUpdate(BaseModel):
    """Schema for updating a LifeArea (all fields optional)"""

    name: str | None = Field(
        None, description="Name of the life area", min_length=1, max_length=100
    )
    weight: int | None = Field(
        None, description="Importance weight as percentage (0-100)", ge=0, le=100
    )
    icon: str | None = Field(None, description="UI icon identifier", max_length=50)
    color: str | None = Field(None, description="UI color preference", max_length=50)
    description: str | None = Field(
        None, description="Description of this life area", max_length=500
    )


class LifeArea(LifeAreaBase):
    id: int = Field(..., description="Unique life area ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class LifeAreaOut(LifeArea):
    """Output schema for LifeArea (same as LifeArea)"""

    pass


## Journal Entry Schemas
class JournalEntryBase(BaseModel):
    content: constr(min_length=1, max_length=10000, strip_whitespace=True) = Field(
        ..., description="Content of the journal entry (1-10000 characters)"
    )

    @validator("content")
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Journal entry content cannot be empty")
        return v.strip()


class JournalEntryCreate(JournalEntryBase):
    """Schema for creating a new Journal Entry"""

    project_id: int | None = Field(
        None, gt=0, description="Associated project ID (positive integer)"
    )
    goal_id: int | None = Field(
        None, gt=0, description="Associated goal ID (positive integer)"
    )
    task_id: int | None = Field(
        None, gt=0, description="Associated task ID (positive integer)"
    )


class JournalEntryUpdate(BaseModel):
    """Schema for updating a Journal Entry"""

    content: constr(min_length=1, max_length=10000, strip_whitespace=True) | None = (
        Field(
            None,
            description="Updated content of the journal entry (1-10000 characters)",
        )
    )

    @validator("content")
    def validate_content(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError("Journal entry content cannot be empty")
        return v


class JournalEntry(JournalEntryBase):
    id: int = Field(..., description="Unique journal entry ID")
    user_id: str = Field(..., description="Owner user ID")
    project_id: int | None = Field(None, description="Associated project ID")
    goal_id: int | None = Field(None, description="Associated goal ID")
    task_id: int | None = Field(None, description="Associated task ID")
    version: int = Field(..., description="Version for sync")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class JournalEntryOut(JournalEntry):
    """Enhanced journal entry output schema with nested relationships"""

    project: Optional["ProjectOut"] = Field(
        None, description="Associated project details"
    )
    goal: Optional["GoalOut"] = Field(None, description="Associated goal details")
    task: Optional["TaskOut"] = Field(None, description="Associated task details")


## Habit Schemas
class RecurrenceRule(BaseModel):
    """Schema for habit recurrence configuration"""

    type: Literal["daily", "weekly", "monthly"] = Field(
        ..., description="Recurrence type"
    )
    target_count: int = Field(
        ..., ge=1, le=100, description="Target count per period (1-100)"
    )
    target_type: Literal["count"] = Field(
        "count", description="Type of target (count-based)"
    )

    # Optional advanced settings
    days_of_week: list[int] | None = Field(
        None, description="Specific days of week (0=Monday, 6=Sunday)"
    )
    days_of_month: list[int] | None = Field(
        None, description="Specific days of month (1-31)"
    )

    @validator("days_of_week")
    def validate_days_of_week(cls, v):
        if v is not None:
            if not all(0 <= day <= 6 for day in v):
                raise ValueError("Days of week must be 0-6 (Monday-Sunday)")
            return sorted(set(v))  # Remove duplicates and sort
        return v

    @validator("days_of_month")
    def validate_days_of_month(cls, v):
        if v is not None:
            if not all(1 <= day <= 31 for day in v):
                raise ValueError("Days of month must be 1-31")
            return sorted(set(v))  # Remove duplicates and sort
        return v


class HabitBase(BaseModel):
    title: constr(min_length=1, max_length=200, strip_whitespace=True) = Field(
        ..., description="Title of the habit (1-200 characters)"
    )
    description: constr(max_length=1000, strip_whitespace=True) | None = Field(
        None, description="Description of the habit (max 1000 characters)"
    )
    recurrence_rule: RecurrenceRule = Field(
        ..., description="Recurrence configuration for the habit"
    )
    is_active: bool | None = Field(
        True, description="Whether the habit is currently active"
    )
    start_date: datetime | None = Field(
        None, description="When to start tracking this habit (defaults to today)"
    )
    end_date: datetime | None = Field(
        None, description="Optional end date for temporary habits"
    )
    icon: constr(max_length=50, strip_whitespace=True) | None = Field(
        None, description="UI icon identifier (max 50 characters)"
    )
    color: constr(max_length=50, strip_whitespace=True) | None = Field(
        None, description="UI color preference (hex or color name, max 50 characters)"
    )
    goal_id: int | None = Field(
        None, gt=0, description="Associated goal ID (positive integer)"
    )
    life_area_id: int | None = Field(
        None, gt=0, description="Associated life area ID (positive integer)"
    )

    @validator("title")
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Habit title cannot be empty")
        return v.strip()

    @validator("description")
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @validator("start_date")
    def validate_start_date(cls, v):
        if v is not None:
            from datetime import datetime, timedelta

            # Don't allow start dates more than 1 year in the past or future
            now = datetime.utcnow()
            min_past = now - timedelta(days=365)
            max_future = now + timedelta(days=365)
            if v < min_past or v > max_future:
                raise ValueError("Start date must be within 1 year of today")
        return v

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if v is not None:
            from datetime import datetime, timedelta

            # End date should be after start date
            if "start_date" in values and values["start_date"] is not None:
                if v <= values["start_date"]:
                    raise ValueError("End date must be after start date")

            # Don't allow end dates more than 10 years in the future
            max_future = datetime.utcnow() + timedelta(days=3650)
            if v > max_future:
                raise ValueError("End date cannot be more than 10 years in the future")
        return v

    @validator("color")
    def validate_color(cls, v):
        if v is not None:
            v = v.strip()
            # Basic hex color validation
            if v.startswith("#") and len(v) in [4, 7]:
                if not all(c in "0123456789ABCDEFabcdef" for c in v[1:]):
                    raise ValueError("Invalid hex color format")
            return v
        return v


class HabitCreate(HabitBase):
    """Schema for creating a new Habit"""

    pass


class HabitUpdate(BaseModel):
    """Schema for updating a Habit (all fields optional)"""

    title: str | None = Field(
        None, description="Title of the habit", min_length=1, max_length=200
    )
    description: str | None = Field(
        None, description="Description of the habit", max_length=1000
    )
    recurrence_rule: RecurrenceRule | None = Field(
        None, description="Recurrence configuration for the habit"
    )
    is_active: bool | None = Field(
        None, description="Whether the habit is currently active"
    )
    start_date: datetime | None = Field(
        None, description="When to start tracking this habit"
    )
    end_date: datetime | None = Field(
        None, description="Optional end date for temporary habits"
    )
    icon: str | None = Field(None, description="UI icon identifier", max_length=50)
    color: str | None = Field(None, description="UI color preference", max_length=50)
    goal_id: int | None = Field(None, description="Associated goal ID")
    life_area_id: int | None = Field(None, description="Associated life area ID")


class Habit(HabitBase):
    id: int = Field(..., description="Unique habit ID")
    user_id: str = Field(..., description="Owner user ID")
    current_streak: int = Field(
        ..., description="Current consecutive completion streak"
    )
    best_streak: int = Field(..., description="Highest streak ever achieved")
    total_completions: int = Field(..., description="Lifetime total completions")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


## HabitCompletion Schemas
class HabitCompletionBase(BaseModel):
    completion_date: datetime | None = Field(
        None, description="Date when habit was completed (defaults to today)"
    )
    notes: constr(max_length=500, strip_whitespace=True) | None = Field(
        None, description="Optional notes about the completion (max 500 characters)"
    )
    duration_minutes: int | None = Field(
        None, ge=1, le=1440, description="Duration in minutes (1-1440, max 24 hours)"
    )
    intensity_rating: int | None = Field(
        None, ge=1, le=10, description="Intensity rating 1-10"
    )

    @validator("notes")
    def validate_notes(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class HabitCompletionCreate(HabitCompletionBase):
    """Schema for creating a habit completion"""

    pass


class HabitCompletionUpdate(BaseModel):
    """Schema for updating a habit completion"""

    notes: str | None = Field(
        None, description="Optional notes about the completion", max_length=500
    )
    duration_minutes: int | None = Field(
        None, ge=1, le=1440, description="Duration in minutes"
    )
    intensity_rating: int | None = Field(
        None, ge=1, le=10, description="Intensity rating 1-10"
    )


class HabitCompletion(HabitCompletionBase):
    id: int = Field(..., description="Unique completion ID")
    habit_id: int = Field(..., description="Associated habit ID")
    completion_time: datetime = Field(..., description="Exact timestamp of completion")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


## Habit Progress Schemas
class HabitProgress(BaseModel):
    """Schema for habit progress within a period"""

    habit_id: int = Field(..., description="Habit ID")
    period_start: datetime = Field(..., description="Start of the period")
    period_end: datetime = Field(..., description="End of the period")
    target_count: int = Field(..., description="Target completions for this period")
    actual_count: int = Field(..., description="Actual completions in this period")
    completion_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Completion rate (0.0-1.0)"
    )
    is_completed: bool = Field(..., description="Whether target was met")
    completions: list[HabitCompletion] = Field(
        default_factory=list, description="Individual completions"
    )


class HabitOut(Habit):
    """Enhanced habit output schema with progress information"""

    current_period_progress: HabitProgress | None = Field(
        None, description="Progress for current period"
    )
    recent_completions: list[HabitCompletion] = Field(
        default_factory=list, description="Recent completions"
    )
    goal: Optional["Goal"] = Field(None, description="Associated goal details")
    life_area: Optional["LifeAreaOut"] = Field(
        None, description="Associated life area details"
    )


class MediaAttachmentBase(BaseModel):
    filename: constr(min_length=1, max_length=255, strip_whitespace=True) = Field(
        ..., description="System filename for the attachment (1-255 characters)"
    )
    original_filename: constr(min_length=1, max_length=255, strip_whitespace=True) = (
        Field(..., description="Original filename from upload (1-255 characters)")
    )
    file_path: constr(min_length=1, max_length=1000, strip_whitespace=True) = Field(
        ..., description="Full path to the stored file (1-1000 characters)"
    )
    file_size: int = Field(
        ..., ge=0, le=1073741824, description="File size in bytes (max 1GB)"  # 1GB max
    )
    content_type: constr(min_length=1, max_length=100, strip_whitespace=True) = Field(
        ..., description="MIME type (e.g., image/jpeg, video/mp4)", alias="mime_type"
    )
    media_type: Literal["image", "video", "audio", "document"] = Field(
        ...,
        description="File category: image, video, audio, document",
        alias="file_type",
    )
    title: constr(max_length=200, strip_whitespace=True) | None = Field(
        None, description="User-defined title for the attachment (max 200 characters)"
    )
    description: constr(max_length=1000, strip_whitespace=True) | None = Field(
        None, description="User description for storytelling (max 1000 characters)"
    )
    duration: int | None = Field(
        None,
        ge=0,
        le=86400,  # 24 hours max
        description="Duration in seconds for video/audio (max 24 hours)",
    )
    width: int | None = Field(
        None,
        ge=1,
        le=8192,  # 8K resolution max
        description="Width in pixels for images/videos (1-8192px)",
    )
    height: int | None = Field(
        None,
        ge=1,
        le=8192,  # 8K resolution max
        description="Height in pixels for images/videos (1-8192px)",
    )

    @validator("content_type")
    def validate_mime_type(cls, v):
        allowed_mime_types = {
            "image": [
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/webp",
                "image/svg+xml",
            ],
            "video": ["video/mp4", "video/webm", "video/avi", "video/mov", "video/wmv"],
            "audio": ["audio/mp3", "audio/wav", "audio/ogg", "audio/aac", "audio/flac"],
            "document": [
                "application/pdf",
                "text/plain",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ],
        }

        # Check if mime type is in any allowed category
        for _category, mime_types in allowed_mime_types.items():
            if v in mime_types:
                return v

        # If not in predefined list, allow but warn
        if "/" not in v:
            raise ValueError("Invalid MIME type format")
        return v

    @validator("media_type")
    def validate_file_type_consistency(cls, v, values):
        if "content_type" in values:
            content_type = values["content_type"]
            if v == "image" and not content_type.startswith("image/"):
                raise ValueError("File type and MIME type mismatch")
            elif v == "video" and not content_type.startswith("video/"):
                raise ValueError("File type and MIME type mismatch")
            elif v == "audio" and not content_type.startswith("audio/"):
                raise ValueError("File type and MIME type mismatch")
        return v


class MediaAttachmentCreate(MediaAttachmentBase):
    """Schema for creating a new MediaAttachment"""

    goal_id: int | None = Field(None, description="ID of associated goal")
    project_id: int | None = Field(None, description="ID of associated project")
    task_id: int | None = Field(None, description="ID of associated task")


class MediaAttachmentUpdate(BaseModel):
    """Schema for updating a MediaAttachment (metadata only)"""

    title: str | None = Field(
        None, description="User-defined title for the attachment", max_length=200
    )
    description: str | None = Field(
        None, description="User description for storytelling", max_length=1000
    )
    goal_id: int | None = Field(None, description="ID of associated goal")
    project_id: int | None = Field(None, description="ID of associated project")
    task_id: int | None = Field(None, description="ID of associated task")


class MediaAttachment(MediaAttachmentBase):
    id: int = Field(..., description="Unique media attachment ID")
    user_id: str = Field(..., description="Owner user ID")
    goal_id: int | None = Field(None, description="Associated goal ID")
    project_id: int | None = Field(None, description="Associated project ID")
    task_id: int | None = Field(None, description="Associated task ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Additional fields for API backward compatibility
    mime_type: str | None = Field(
        None, description="MIME type (alias for content_type)"
    )
    file_type: str | None = Field(
        None, description="File type category (alias for media_type)"
    )

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
    tone: Literal["friendly", "coach", "minimal", "professional"] | None = Field(
        "friendly", description="Communication tone preference"
    )

    # Notification preferences
    notification_time: time | None = Field(
        None, description="Preferred time for daily notifications (HH:MM)"
    )
    notifications_enabled: bool | None = Field(
        True, description="Enable/disable notifications"
    )
    email_notifications: bool | None = Field(
        False, description="Enable/disable email notifications"
    )

    # Content and visualization preferences
    prefers_video: bool | None = Field(True, description="Prefers video content")
    prefers_audio: bool | None = Field(False, description="Prefers audio content")
    default_view: Literal["list", "card", "timeline"] | None = Field(
        "card", description="Default view mode"
    )

    # Feature preferences
    mood_tracking_enabled: bool | None = Field(
        False, description="Enable mood tracking feature"
    )
    progress_charts_enabled: bool | None = Field(
        True, description="Enable progress charts"
    )
    ai_suggestions_enabled: bool | None = Field(
        True, description="Enable AI suggestions"
    )

    # Default associations
    default_life_area_id: int | None = Field(
        None, description="Default life area ID for new goals/tasks"
    )

    # Privacy and data preferences
    data_sharing_enabled: bool | None = Field(
        False, description="Allow data sharing for improvements"
    )
    analytics_enabled: bool | None = Field(
        True, description="Enable analytics tracking"
    )


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

    goals: list["Goal"] = Field(default_factory=list, description="Associated goals")
    tasks: list["Task"] = Field(default_factory=list, description="Associated tasks")
    media: list["MediaAttachmentOut"] = Field(
        default_factory=list, description="Associated media attachments"
    )
    life_area: Optional["LifeAreaOut"] = Field(
        None, description="Associated life area details"
    )

    # Hierarchy fields (without circular references)
    parent_id: int | None = Field(None, description="Parent project ID")
    hierarchy_level: int | None = Field(
        None, ge=0, description="Hierarchy level (0 = root)"
    )
    children_count: int | None = Field(
        None, ge=0, description="Number of direct children"
    )


class TaskOut(Task):
    """Enhanced task output schema with nested relationships"""

    media: list["MediaAttachmentOut"] = Field(
        default_factory=list, description="Associated media attachments"
    )
    life_area: Optional["LifeAreaOut"] = Field(
        None, description="Associated life area details"
    )
    project: Optional["ProjectOut"] = Field(
        None, description="Associated project details"
    )

    # Hierarchy fields (without circular references)
    parent_id: int | None = Field(None, description="Parent task ID")
    hierarchy_level: int | None = Field(
        None, ge=0, description="Hierarchy level (0 = root)"
    )
    children_count: int | None = Field(
        None, ge=0, description="Number of direct children"
    )


class GoalOut(Goal):
    """Enhanced goal output schema with nested relationships"""

    tasks: list["TaskOut"] = Field(default_factory=list, description="Associated tasks")
    media: list["MediaAttachmentOut"] = Field(
        default_factory=list, description="Associated media attachments"
    )
    life_area: Optional["LifeAreaOut"] = Field(
        None, description="Associated life area details"
    )
    project: Optional["ProjectOut"] = Field(
        None, description="Associated project details"
    )

    # Hierarchy fields (without circular references)
    parent_id: int | None = Field(None, description="Parent goal ID")
    hierarchy_level: int | None = Field(
        None, ge=0, description="Hierarchy level (0 = root)"
    )
    children_count: int | None = Field(
        None, ge=0, description="Number of direct children"
    )


class UserPreferencesOut(UserPreferences):
    """Enhanced user preferences output schema"""

    default_life_area: Optional["LifeAreaOut"] = Field(
        None, description="Default life area details"
    )


## UserPreferencesHistory Schemas
class UserPreferencesHistoryItem(BaseModel):
    """Schema for individual preference change history item"""

    id: str = Field(..., description="Unique history entry ID")
    preference_name: str = Field(..., description="Name of the preference that changed")
    old_value: str | None = Field(None, description="Previous value (as string)")
    new_value: str | None = Field(None, description="New value (as string)")
    changed_at: datetime = Field(..., description="When the change occurred")

    class Config:
        from_attributes = True


class UserPreferencesChangeSummary(BaseModel):
    """Schema for user preferences change summary and analytics"""

    total_changes: int = Field(..., description="Total number of preference changes")
    days_analyzed: int = Field(..., description="Number of days analyzed")
    preferences_changed: list[str] = Field(
        ..., description="List of preference names that were changed"
    )
    change_counts: dict[str, int] = Field(
        ..., description="Count of changes per preference"
    )
    most_changed_preference: dict[str, Any] | None = Field(
        None, description="Most frequently changed preference"
    )
    latest_change: dict[str, Any] | None = Field(
        None, description="Details of the most recent change"
    )


class UserOut(User):
    """Enhanced user output schema with nested relationships"""

    preferences: Optional["UserPreferencesOut"] = Field(
        None, description="User preferences"
    )
    created_at: datetime | None = Field(
        None, description="Account creation timestamp"
    )

    class Config:
        from_attributes = True


## FeedbackLog Schemas
class FeedbackLogBase(BaseModel):
    # Context information
    context_type: constr(min_length=1, max_length=50, strip_whitespace=True) = Field(
        ...,
        description="Type of context (task, goal, plan, suggestion, ui_interaction, etc.)",
    )
    context_id: constr(max_length=100, strip_whitespace=True) | None = Field(
        None, description="ID of the related entity (goal_id, task_id, etc.)"
    )
    context_data: dict[str, Any] | None = Field(
        None, description="Additional context data (query, response, etc.)"
    )

    # Feedback details
    feedback_type: Literal["positive", "negative", "neutral"] = Field(
        ..., description="Type of feedback"
    )
    feedback_value: float | None = Field(
        None, ge=-1.0, le=1.0, description="Numeric feedback score (-1.0 to 1.0)"
    )
    comment: constr(max_length=1000, strip_whitespace=True) | None = Field(
        None, description="Optional user comment (max 1000 characters)"
    )

    # ML/RLHF specific fields
    action_taken: dict[str, Any] | None = Field(
        None, description="What action was taken (for RL)"
    )
    reward_signal: float | None = Field(
        None, ge=-10.0, le=10.0, description="Computed reward signal (-10.0 to 10.0)"
    )
    model_version: constr(max_length=50, strip_whitespace=True) | None = Field(
        None, description="Version of model that generated the response"
    )

    # Metadata
    session_id: constr(max_length=100, strip_whitespace=True) | None = Field(
        None, description="Session identifier for grouping related feedback"
    )
    device_info: dict[str, Any] | None = Field(
        None, description="Device/platform information"
    )
    feature_flags: dict[str, Any] | None = Field(
        None, description="Active feature flags during interaction"
    )

    @validator("context_data")
    def validate_context_data(cls, v):
        if v is not None:
            # Limit context data size to prevent abuse
            if len(str(v)) > 10000:  # 10KB limit
                raise ValueError("Context data too large (max 10KB)")
        return v

    @validator("device_info")
    def validate_device_info(cls, v):
        if v is not None:
            # Ensure device info doesn't contain sensitive data
            sensitive_keys = ["password", "token", "key", "secret"]
            for key in v.keys():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    raise ValueError("Device info cannot contain sensitive data")
        return v


class FeedbackLogCreate(FeedbackLogBase):
    """Schema for creating feedback logs"""

    pass


class FeedbackLogUpdate(BaseModel):
    """Schema for updating feedback logs - limited fields"""

    comment: str | None = Field(
        None, max_length=1000, description="Updated user comment"
    )
    processed_at: datetime | None = Field(
        None, description="When feedback was processed for training"
    )


class FeedbackLog(FeedbackLogBase):
    id: str = Field(..., description="Unique feedback log ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    processed_at: datetime | None = Field(
        None, description="When feedback was processed for training"
    )

    class Config:
        from_attributes = True


class FeedbackLogSummary(BaseModel):
    """Summary statistics for feedback logs"""

    total_feedback: int = Field(..., description="Total number of feedback entries")
    positive_count: int = Field(..., description="Number of positive feedback entries")
    negative_count: int = Field(..., description="Number of negative feedback entries")
    neutral_count: int = Field(..., description="Number of neutral feedback entries")
    average_score: float | None = Field(None, description="Average feedback score")
    context_breakdown: dict[str, int] = Field(
        ..., description="Breakdown by context type"
    )
    recent_feedback: list[FeedbackLog] = Field(
        ..., description="Most recent feedback entries"
    )


## Tag Schemas
class TagBase(BaseModel):
    name: constr(min_length=1, max_length=50, strip_whitespace=True) = Field(
        ..., description="Name of the tag (1-50 characters)"
    )
    color: constr(max_length=7, strip_whitespace=True) | None = Field(
        None, description="Hex color code for UI (e.g., '#FF5722')"
    )

    @validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")
        return v.strip()

    @validator("color")
    def validate_color(cls, v):
        if v is not None:
            v = v.strip()
            # Basic hex color validation
            if v.startswith("#") and len(v) == 7:
                if not all(c in "0123456789ABCDEFabcdef" for c in v[1:]):
                    raise ValueError("Invalid hex color format")
            else:
                raise ValueError("Color must be a hex code like #FF5722")
            return v
        return v


class TagCreate(TagBase):
    """Schema for creating a new Tag"""

    pass


class TagUpdate(BaseModel):
    """Schema for updating a Tag (all fields optional)"""

    name: str | None = Field(
        None, description="Name of the tag", min_length=1, max_length=50
    )
    color: str | None = Field(
        None, description="Hex color code for UI", max_length=7
    )

    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError("Tag name cannot be empty")
        return v

    @validator("color")
    def validate_color(cls, v):
        if v is not None:
            v = v.strip()
            # Basic hex color validation
            if v.startswith("#") and len(v) == 7:
                if not all(c in "0123456789ABCDEFabcdef" for c in v[1:]):
                    raise ValueError("Invalid hex color format")
            else:
                raise ValueError("Color must be a hex code like #FF5722")
            return v
        return v


class Tag(TagBase):
    id: int = Field(..., description="Unique tag ID")
    user_id: str = Field(..., description="Owner user ID")
    version: int = Field(..., description="Version for sync")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class TagOut(Tag):
    """Enhanced tag output schema"""

    usage_count: int | None = Field(
        None, description="Number of entities using this tag"
    )


## StorySession Schemas
class StorySessionBase(BaseModel):
    # Content information
    title: str | None = Field(
        None, max_length=200, description="User-defined title for the story session"
    )
    generated_text: str | None = Field(
        None, description="AI-generated narrative text"
    )
    video_url: str | None = Field(None, description="URL to generated video")
    audio_url: str | None = Field(
        None, description="URL to generated audio/narration"
    )
    thumbnail_url: str | None = Field(None, description="URL to video thumbnail")

    # Generation parameters
    summary_period: str | None = Field(
        None, description="Period type: weekly, monthly, project-based, custom"
    )
    period_start: datetime | None = Field(
        None, description="Start of the period being summarized"
    )
    period_end: datetime | None = Field(
        None, description="End of the period being summarized"
    )
    content_type: Literal["summary", "story", "reflection", "achievement"] | None = (
        Field("summary", description="Type of content generated")
    )

    # Social media and distribution
    posted_to: list[str] | None = Field(
        default_factory=list, description="Platforms where content was posted"
    )
    posting_status: Literal["draft", "scheduled", "posted", "failed"] | None = Field(
        "draft", description="Current posting status"
    )
    scheduled_post_time: datetime | None = Field(
        None, description="When content is scheduled to be posted"
    )

    # Generation metadata
    generation_prompt: str | None = Field(
        None, description="The prompt used for generation"
    )
    model_version: str | None = Field(None, description="AI model version used")
    generation_params: dict[str, Any] | None = Field(
        None, description="Parameters used for generation"
    )
    word_count: int | None = Field(
        None, ge=0, description="Word count of generated text"
    )
    estimated_read_time: int | None = Field(
        None, ge=0, description="Estimated reading time in seconds"
    )

    # Related content
    source_goals: list[int] | None = Field(
        default_factory=list, description="Goal IDs that contributed to this story"
    )
    source_tasks: list[int] | None = Field(
        default_factory=list, description="Task IDs that contributed to this story"
    )
    source_life_areas: list[int] | None = Field(
        default_factory=list, description="Life area IDs featured in this story"
    )

    # Engagement and analytics
    view_count: int | None = Field(0, ge=0, description="Number of times viewed")
    like_count: int | None = Field(0, ge=0, description="Number of likes")
    share_count: int | None = Field(0, ge=0, description="Number of shares")
    engagement_data: dict[str, Any] | None = Field(
        None, description="Additional engagement metrics"
    )

    # Quality and user feedback
    user_rating: float | None = Field(
        None, ge=1.0, le=5.0, description="User rating 1-5 stars"
    )
    user_notes: str | None = Field(
        None, max_length=1000, description="User notes about the story"
    )
    regeneration_count: int | None = Field(
        0, ge=0, description="How many times this was regenerated"
    )

    # Processing status
    processing_status: Literal["pending", "generating", "completed", "failed"] | None = Field("pending", description="Current processing status")
    error_message: str | None = Field(
        None, description="Error message if generation failed"
    )


class StorySessionCreate(StorySessionBase):
    """Schema for creating story sessions"""

    pass


class StorySessionUpdate(BaseModel):
    """Schema for updating story sessions - all fields optional"""

    title: str | None = Field(
        None, max_length=200, description="User-defined title for the story session"
    )
    generated_text: str | None = Field(
        None, description="AI-generated narrative text"
    )
    video_url: str | None = Field(None, description="URL to generated video")
    audio_url: str | None = Field(
        None, description="URL to generated audio/narration"
    )
    thumbnail_url: str | None = Field(None, description="URL to video thumbnail")
    summary_period: str | None = Field(
        None, description="Period type: weekly, monthly, project-based, custom"
    )
    period_start: datetime | None = Field(
        None, description="Start of the period being summarized"
    )
    period_end: datetime | None = Field(
        None, description="End of the period being summarized"
    )
    content_type: Literal["summary", "story", "reflection", "achievement"] | None = (
        Field(None, description="Type of content generated")
    )
    posted_to: list[str] | None = Field(
        None, description="Platforms where content was posted"
    )
    posting_status: Literal["draft", "scheduled", "posted", "failed"] | None = Field(
        None, description="Current posting status"
    )
    scheduled_post_time: datetime | None = Field(
        None, description="When content is scheduled to be posted"
    )
    generation_prompt: str | None = Field(
        None, description="The prompt used for generation"
    )
    model_version: str | None = Field(None, description="AI model version used")
    generation_params: dict[str, Any] | None = Field(
        None, description="Parameters used for generation"
    )
    word_count: int | None = Field(
        None, ge=0, description="Word count of generated text"
    )
    estimated_read_time: int | None = Field(
        None, ge=0, description="Estimated reading time in seconds"
    )
    source_goals: list[int] | None = Field(
        None, description="Goal IDs that contributed to this story"
    )
    source_tasks: list[int] | None = Field(
        None, description="Task IDs that contributed to this story"
    )
    source_life_areas: list[int] | None = Field(
        None, description="Life area IDs featured in this story"
    )
    view_count: int | None = Field(None, ge=0, description="Number of times viewed")
    like_count: int | None = Field(None, ge=0, description="Number of likes")
    share_count: int | None = Field(None, ge=0, description="Number of shares")
    engagement_data: dict[str, Any] | None = Field(
        None, description="Additional engagement metrics"
    )
    user_rating: float | None = Field(
        None, ge=1.0, le=5.0, description="User rating 1-5 stars"
    )
    user_notes: str | None = Field(
        None, max_length=1000, description="User notes about the story"
    )
    regeneration_count: int | None = Field(
        None, ge=0, description="How many times this was regenerated"
    )
    processing_status: Literal["pending", "generating", "completed", "failed"] | None = Field(None, description="Current processing status")
    error_message: str | None = Field(
        None, description="Error message if generation failed"
    )
    generated_at: datetime | None = Field(
        None, description="When generation was completed"
    )
    posted_at: datetime | None = Field(
        None, description="When content was actually posted"
    )


class StorySession(StorySessionBase):
    id: str = Field(..., description="Unique story session ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    generated_at: datetime | None = Field(
        None, description="When generation was completed"
    )
    posted_at: datetime | None = Field(
        None, description="When content was actually posted"
    )

    class Config:
        from_attributes = True


class StorySessionSummary(BaseModel):
    """Summary statistics for story sessions"""

    total_sessions: int = Field(..., description="Total number of story sessions")
    by_content_type: dict[str, int] = Field(
        ..., description="Breakdown by content type"
    )
    by_posting_status: dict[str, int] = Field(
        ..., description="Breakdown by posting status"
    )
    by_processing_status: dict[str, int] = Field(
        ..., description="Breakdown by processing status"
    )
    total_word_count: int = Field(..., description="Total words generated")
    average_rating: float | None = Field(None, description="Average user rating")
    recent_sessions: list[StorySession] = Field(
        ..., description="Most recent story sessions"
    )


class GenerationRequest(BaseModel):
    """Schema for requesting story generation"""

    title: str | None = Field(
        None, max_length=200, description="Title for the story session"
    )
    summary_period: str = Field(
        ..., description="Period type: weekly, monthly, project-based, custom"
    )
    period_start: datetime | None = Field(
        None, description="Start of the period to summarize"
    )
    period_end: datetime | None = Field(
        None, description="End of the period to summarize"
    )
    content_type: Literal["summary", "story", "reflection", "achievement"] = Field(
        "summary", description="Type of content to generate"
    )
    generation_prompt: str | None = Field(
        None, description="Custom prompt for generation"
    )
    include_goals: bool = Field(True, description="Include goals in the generation")
    include_tasks: bool = Field(True, description="Include tasks in the generation")
    include_life_areas: list[int] | None = Field(
        None, description="Specific life areas to focus on"
    )
    generation_params: dict[str, Any] | None = Field(
        None, description="Custom generation parameters"
    )


class PublishRequest(BaseModel):
    """Schema for publishing story content"""

    platforms: list[str] = Field(
        ..., min_items=1, description="Platforms to publish to"
    )
    scheduled_time: datetime | None = Field(
        None, description="When to schedule the post"
    )
    custom_message: str | None = Field(
        None, max_length=500, description="Custom message for the post"
    )


## Hierarchy Schemas
class HierarchyTreeNode(BaseModel):
    """Schema for hierarchical tree representation of goals/projects"""

    id: int = Field(..., description="Entity ID")
    title: str = Field(..., description="Entity title")
    entity_type: Literal["goal", "project"] = Field(..., description="Type of entity")
    level: int = Field(..., ge=0, description="Hierarchy level (0 = root)")
    parent_id: int | None = Field(None, description="Parent entity ID")
    children: list["HierarchyTreeNode"] = Field(
        default_factory=list, description="Child entities"
    )
    status: str | None = Field(None, description="Current status")
    progress: float | None = Field(
        None, ge=0.0, le=100.0, description="Progress percentage"
    )
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class HierarchyMoveRequest(BaseModel):
    """Schema for moving entities in hierarchy"""

    parent_id: int | None = Field(
        None, description="New parent ID (null for root level)"
    )

    @validator("parent_id")
    def validate_parent_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Parent ID must be a positive integer")
        return v


class HierarchyPathItem(BaseModel):
    """Schema for hierarchy path representation"""

    id: int = Field(..., description="Entity ID")
    title: str = Field(..., description="Entity title")
    entity_type: Literal["goal", "project"] = Field(..., description="Type of entity")
    level: int = Field(..., ge=0, description="Hierarchy level")


class HierarchyStats(BaseModel):
    """Schema for hierarchy statistics"""

    total_items: int = Field(..., ge=0, description="Total items in hierarchy")
    max_depth: int = Field(..., ge=0, description="Maximum depth level")
    root_items: int = Field(..., ge=0, description="Number of root level items")
    avg_children_per_parent: float | None = Field(
        None, ge=0.0, description="Average children per parent"
    )
    completion_rate_by_level: dict[int, float] = Field(
        default_factory=dict, description="Completion rate by hierarchy level"
    )


class HierarchyOverview(BaseModel):
    """Schema for complete hierarchy overview"""

    goals: HierarchyStats = Field(..., description="Goals hierarchy statistics")
    projects: HierarchyStats = Field(..., description="Projects hierarchy statistics")
    cross_references: int = Field(
        ..., ge=0, description="Number of goals linked to projects"
    )


# Rebuild models to resolve forward references for Pydantic V2
ProjectOut.model_rebuild()
TaskOut.model_rebuild()
GoalOut.model_rebuild()
JournalEntryOut.model_rebuild()
HabitOut.model_rebuild()
UserPreferencesOut.model_rebuild()
UserOut.model_rebuild()
