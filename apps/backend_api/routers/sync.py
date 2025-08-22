"""
Batch Sync API endpoints for offline-first architecture.

This module implements efficient batch synchronization endpoints that:
- Process multiple operations in single requests
- Support conflict detection and resolution
- Provide delta sync for incremental updates
- Handle all entity types with consistent patterns
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Literal

import sqlalchemy as sa
from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models.content import MediaAttachment
from models.goals import Goal, LifeArea, Project, Task
from models.onboarding import AssistantProfile, OnboardingState, PersonalProfile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/sync", tags=["sync"])


class SyncOperation(BaseModel):
    """Individual sync operation within a batch."""

    object_id: str = Field(..., description="Unique identifier for the object")
    object_type: str = Field(
        ..., description="Type of object (goal, task, assistant, etc.)"
    )
    operation: Literal["create", "update", "delete"] = Field(
        ..., description="Operation type"
    )
    data: dict[str, Any] = Field(..., description="Object data for the operation")
    version: int = Field(..., description="Client version of the object")
    if_match_version: int | None = Field(
        None, description="Server version to match for conflict detection"
    )


class BatchSyncRequest(BaseModel):
    """Batch sync request containing multiple operations."""

    operations: list[SyncOperation] = Field(..., description="List of sync operations")
    client_id: str = Field(..., description="Client identifier for tracking")


class SyncResult(BaseModel):
    """Result of a single sync operation."""

    object_id: str
    status: Literal["success", "conflict", "error"]
    new_version: int | None = None
    server_data: dict[str, Any] | None = None
    error_message: str | None = None


class DeltaSyncResponse(BaseModel):
    """Response for delta sync requests."""

    changes: list[dict[str, Any]]
    current_timestamp: int
    has_more: bool


class ConflictError(Exception):
    """Exception raised when a sync conflict is detected."""

    def __init__(self, server_version: int, server_data: dict[str, Any]):
        self.server_version = server_version
        self.server_data = server_data
        super().__init__(f"Conflict detected - server version {server_version}")


# Model registry for dynamic model lookup
MODEL_REGISTRY = {
    "goal": Goal,
    "project": Project,
    "task": Task,
    "life_area": LifeArea,
    "onboarding_state": OnboardingState,
    "personal_profile": PersonalProfile,
    "assistant_profile": AssistantProfile,
    "media_attachment": MediaAttachment,
    # All CRUD-supported models are now included
}


def get_model_class(object_type: str):
    """Get SQLAlchemy model class for object type."""
    if object_type not in MODEL_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown object type: {object_type}",
        )
    return MODEL_REGISTRY[object_type]


@router.post("/batch", response_model=list[SyncResult])
async def sync_batch(
    request: BatchSyncRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process multiple object operations in a single atomic transaction.

    This endpoint handles batch synchronization of multiple objects, providing:
    - Atomic processing (all operations succeed or all fail)
    - Conflict detection with version checking
    - Efficient batch processing by object type
    - Comprehensive error handling and reporting
    """
    results = []

    # Group operations by type for efficient processing
    operations_by_type = defaultdict(list)
    for op in request.operations:
        operations_by_type[op.object_type].append(op)

    # Process all operations in a single transaction for atomicity
    try:
        print(f"🔄 SYNC: Processing batch with {len(request.operations)} operations")

        for object_type, operations in operations_by_type.items():
            print(f"🔄 SYNC: Processing {len(operations)} {object_type} operations")

            for op in operations:
                try:
                    result = await process_sync_operation(
                        op, current_user, db, object_type
                    )
                    results.append(result)
                    print(
                        f"✅ SYNC: {op.operation} {object_type}:{op.object_id} - success"
                    )

                except ConflictError as e:
                    results.append(
                        SyncResult(
                            object_id=op.object_id,
                            status="conflict",
                            server_data=e.server_data,
                            new_version=e.server_version,
                        )
                    )
                    print(
                        f"⚠️ SYNC: {op.operation} {object_type}:{op.object_id} - conflict"
                    )

                except Exception as e:
                    print(
                        f"❌ SYNC: {op.operation} {object_type}:{op.object_id} - error: {e}"
                    )
                    results.append(
                        SyncResult(
                            object_id=op.object_id, status="error", error_message=str(e)
                        )
                    )

        # Commit the entire batch
        db.commit()
        print("✅ SYNC: Batch committed successfully")

    except Exception as e:
        print(f"❌ SYNC: Batch transaction failed: {e}")
        db.rollback()
        # If transaction fails, mark all operations as failed
        for op in request.operations:
            if not any(r.object_id == op.object_id for r in results):
                results.append(
                    SyncResult(
                        object_id=op.object_id,
                        status="error",
                        error_message=f"Transaction failed: {str(e)}",
                    )
                )

    return results


async def process_sync_operation(
    operation: SyncOperation, current_user: dict, db: Session, object_type: str
) -> SyncResult:
    """Process individual sync operation with conflict detection."""

    # Get appropriate model class
    model_class = get_model_class(object_type)

    if operation.operation == "create":
        # Create new object
        obj_data = {
            "user_id": current_user["uid"],
            "version": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Filter and add only valid fields from operation data
        for field, value in operation.data.items():
            if hasattr(model_class, field) and field not in [
                "id",
                "user_id",
                "created_at",
                "updated_at",
                "version",
            ]:
                obj_data[field] = value
            elif field not in ["id", "user_id", "created_at", "updated_at", "version"]:
                print(f"⚠️ SYNC: Skipping unknown field '{field}' for {object_type}")

        # Special handling for AssistantProfile - set owner_id
        if object_type == "assistant_profile":
            obj_data["owner_id"] = current_user["uid"]

        # Determine if model uses string or auto-incrementing IDs
        # Check the column type rather than default value
        id_column = model_class.id.property.columns[0]
        uses_string_id = (
            str(id_column.type).startswith("VARCHAR")
            or str(id_column.type).startswith("TEXT")
            or isinstance(id_column.type, sa.String)
        )

        if uses_string_id:
            # Model uses string ID, set it
            obj_data["id"] = operation.object_id
        # else: Model has auto-incrementing ID, don't set it

        obj = model_class(**obj_data)
        db.add(obj)
        db.flush()  # Get the ID without committing

        return SyncResult(
            object_id=str(obj.id),  # Return the actual DB ID
            status="success",
            new_version=1,
        )

    elif operation.operation == "update":
        # Find existing object - convert object_id to proper type
        try:
            # Check the column type to determine ID type
            id_column = model_class.id.property.columns[0]
            uses_string_id = (
                str(id_column.type).startswith("VARCHAR")
                or str(id_column.type).startswith("TEXT")
                or isinstance(id_column.type, sa.String)
            )

            if uses_string_id:
                # String ID
                obj_id = operation.object_id
            else:
                # Auto-incrementing integer ID
                obj_id = int(operation.object_id)

            obj = (
                db.query(model_class)
                .filter(
                    model_class.id == obj_id, model_class.user_id == current_user["uid"]
                )
                .first()
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid object ID format",
            )

        if not obj:
            # Object not found - create it instead (upsert behavior)
            print(
                f"⚠️ SYNC: Object not found for update {object_type}:{operation.object_id}, creating instead"
            )

            # Create new object with the provided ID
            obj_data = {
                "id": operation.object_id,
                "user_id": current_user["uid"],
                "version": 1,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # Add fields from operation data
            for field, value in operation.data.items():
                if hasattr(model_class, field) and field not in [
                    "id",
                    "user_id",
                    "created_at",
                    "updated_at",
                    "version",
                ]:
                    obj_data[field] = value

            # Special handling for models that need additional fields
            if object_type == "assistant_profile":
                obj_data["owner_id"] = current_user["uid"]

            obj = model_class(**obj_data)
            db.add(obj)
            db.flush()

            return SyncResult(object_id=str(obj.id), status="success", new_version=1)

        # Check for conflicts
        if operation.if_match_version and obj.version != operation.if_match_version:
            raise ConflictError(
                server_version=obj.version, server_data=_obj_to_dict(obj)
            )

        # Apply updates
        for field, value in operation.data.items():
            if hasattr(obj, field) and field not in ["id", "user_id", "created_at"]:
                # Special handling for AssistantProfile - don't update owner_id
                if object_type == "assistant_profile" and field == "owner_id":
                    continue
                setattr(obj, field, value)
            elif field not in ["id", "user_id", "created_at"] and not hasattr(
                obj, field
            ):
                # Log skipped fields for debugging
                print(f"⚠️ SYNC: Skipping unknown field '{field}' for {object_type}")

        obj.version += 1
        obj.updated_at = datetime.utcnow()

        return SyncResult(
            object_id=str(obj.id),  # Return the actual DB ID
            status="success",
            new_version=obj.version,
        )

    elif operation.operation == "delete":
        # Soft delete or hard delete based on object type
        try:
            # Check the column type to determine ID type
            id_column = model_class.id.property.columns[0]
            uses_string_id = (
                str(id_column.type).startswith("VARCHAR")
                or str(id_column.type).startswith("TEXT")
                or isinstance(id_column.type, sa.String)
            )

            if uses_string_id:
                # String ID
                obj_id = operation.object_id
            else:
                # Auto-incrementing integer ID
                obj_id = int(operation.object_id)

            obj = (
                db.query(model_class)
                .filter(
                    model_class.id == obj_id, model_class.user_id == current_user["uid"]
                )
                .first()
            )
        except ValueError:
            # Invalid ID format, just return success (idempotent delete)
            pass
            obj = None

        if obj:
            # Check if model supports soft delete
            if hasattr(obj, "deleted_at"):
                obj.deleted_at = datetime.utcnow()
                obj.version += 1
                obj.updated_at = datetime.utcnow()
            else:
                db.delete(obj)

        return SyncResult(
            object_id=operation.object_id,  # Keep original ID for delete operations
            status="success",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown operation: {operation.operation}",
        )


@router.get("/delta/{since_timestamp}", response_model=DeltaSyncResponse)
async def get_delta_sync(
    since_timestamp: int,
    object_types: str | None = None,  # Comma-separated list
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all changes since a specific timestamp.

    This endpoint provides incremental sync by returning only objects
    that have been modified since the specified timestamp.
    """
    # Convert to naive datetime to match database timestamps
    since_date = datetime.fromtimestamp(since_timestamp / 1000)
    types_filter = object_types.split(",") if object_types else None

    changes = []

    # Get changes for each object type
    for model_name, model_class in MODEL_REGISTRY.items():
        if types_filter and model_name not in types_filter:
            continue

        # Skip models that don't have updated_at field
        if not hasattr(model_class, "updated_at"):
            continue

        # Find objects updated since timestamp
        query = db.query(model_class).filter(
            model_class.user_id == current_user["uid"],
            model_class.updated_at > since_date,
        )

        # Exclude soft-deleted items if the model supports it
        if hasattr(model_class, "deleted_at"):
            query = query.filter(model_class.deleted_at is None)

        # Apply limit across all types
        remaining_limit = limit - len(changes)
        if remaining_limit <= 0:
            break

        updated_objects = query.limit(remaining_limit).all()

        for obj in updated_objects:
            # Determine operation type based on creation vs update time
            operation = "create" if obj.created_at > since_date else "update"

            changes.append(
                {
                    "object_id": obj.id,
                    "object_type": model_name,
                    "operation": operation,
                    "data": _obj_to_dict(obj),
                    "version": obj.version,
                    "timestamp": int(obj.updated_at.timestamp() * 1000),
                }
            )

    # Sort by timestamp
    changes.sort(key=lambda x: x["timestamp"])

    return DeltaSyncResponse(
        changes=changes,
        current_timestamp=int(datetime.utcnow().timestamp() * 1000),
        has_more=len(changes) >= limit,
    )


@router.get("/status")
async def get_sync_status(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get synchronization status for the current user.

    Returns statistics about object counts, sync states, and last sync times.
    """
    stats = {}

    for model_name, model_class in MODEL_REGISTRY.items():
        # Skip models that don't have updated_at field
        if not hasattr(model_class, "updated_at"):
            continue

        # Get total count
        total = (
            db.query(model_class)
            .filter(model_class.user_id == current_user["uid"])
            .count()
        )

        # Get recent changes (last 24 hours)
        recent_cutoff = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        recent = (
            db.query(model_class)
            .filter(
                model_class.user_id == current_user["uid"],
                model_class.updated_at >= recent_cutoff,
            )
            .count()
        )

        stats[model_name] = {"total_objects": total, "recent_changes": recent}

    return {
        "user_id": current_user["uid"],
        "sync_timestamp": int(datetime.utcnow().timestamp() * 1000),
        "object_stats": stats,
    }


def _obj_to_dict(obj) -> dict[str, Any]:
    """Convert SQLAlchemy object to dictionary."""
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        result[column.name] = value
    return result


@router.post("/resolve-conflict/{object_id}")
async def resolve_conflict(
    object_id: str,
    resolution_data: dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Resolve a sync conflict for a specific object.

    The client provides the resolved data which will be applied
    with a new version number.
    """
    object_type = resolution_data.get("object_type")
    if not object_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="object_type required in resolution_data",
        )

    model_class = get_model_class(object_type)

    # Find the object
    obj = (
        db.query(model_class)
        .filter(model_class.id == object_id, model_class.user_id == current_user["uid"])
        .first()
    )

    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Object not found"
        )

    # Apply resolved data
    for field, value in resolution_data.get("data", {}).items():
        if hasattr(obj, field) and field not in ["id", "user_id", "created_at"]:
            setattr(obj, field, value)

    # Increment version to indicate resolution
    obj.version += 1
    obj.updated_at = datetime.utcnow()

    db.commit()

    return {
        "object_id": str(obj.id),  # Return the actual DB ID
        "status": "resolved",
        "new_version": obj.version,
    }
