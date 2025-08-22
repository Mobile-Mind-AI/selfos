"""Journal entry routes - API endpoints for journal/notes functionality."""

from datetime import datetime

from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas import (
    JournalEntry,
    JournalEntryCreate,
    JournalEntryUpdate,
)
from services.journal_service import JournalService
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/", response_model=JournalEntry, status_code=201)
def create_journal_entry(
    entry_data: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create a new journal entry

    The entry can optionally be associated with a project, goal, or task.
    If associations are provided, they must exist and belong to the current user.

    Args:
        entry_data: Journal entry creation data
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Created journal entry

    Raises:
        400: If referenced project/goal/task doesn't exist or access denied
        422: If validation fails
    """
    try:
        entry = JournalService.create_entry(db, current_user["uid"], entry_data)
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[JournalEntry])
def get_journal_entries(
    project_id: int | None = Query(None, description="Filter by project ID"),
    goal_id: int | None = Query(None, description="Filter by goal ID"),
    task_id: int | None = Query(None, description="Filter by task ID"),
    search: str | None = Query(None, description="Search in content"),
    start_date: datetime | None = Query(
        None, description="Filter entries created after this date"
    ),
    end_date: datetime | None = Query(
        None, description="Filter entries created before this date"
    ),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of entries to return"
    ),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get journal entries with optional filtering

    Supports filtering by associated entities, content search, date ranges,
    and pagination. Results are ordered by creation date (most recent first).

    Args:
        project_id: Filter by project ID
        goal_id: Filter by goal ID
        task_id: Filter by task ID
        search: Search term for content
        start_date: Filter entries created after this date
        end_date: Filter entries created before this date
        limit: Maximum number of entries to return (1-100)
        offset: Number of entries to skip for pagination
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of journal entries matching filters
    """
    entries = JournalService.get_entries(
        db=db,
        user_id=current_user["uid"],
        project_id=project_id,
        goal_id=goal_id,
        task_id=task_id,
        limit=limit,
        offset=offset,
        search_content=search,
        start_date=start_date,
        end_date=end_date,
    )
    return entries


@router.get("/count")
def get_journal_entry_count(
    project_id: int | None = Query(None, description="Filter by project ID"),
    goal_id: int | None = Query(None, description="Filter by goal ID"),
    task_id: int | None = Query(None, description="Filter by task ID"),
    start_date: datetime | None = Query(
        None, description="Filter entries created after this date"
    ),
    end_date: datetime | None = Query(
        None, description="Filter entries created before this date"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get count of journal entries with optional filtering

    Useful for pagination and displaying total counts in UI.
    Uses the same filters as the main GET endpoint.

    Args:
        project_id: Filter by project ID
        goal_id: Filter by goal ID
        task_id: Filter by task ID
        start_date: Filter entries created after this date
        end_date: Filter entries created before this date
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Dictionary with count information
    """
    count = JournalService.get_entry_count(
        db=db,
        user_id=current_user["uid"],
        project_id=project_id,
        goal_id=goal_id,
        task_id=task_id,
        start_date=start_date,
        end_date=end_date,
    )
    return {"count": count}


@router.get("/recent", response_model=list[JournalEntry])
def get_recent_journal_entries(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of entries to return"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get recent journal entries

    Retrieves journal entries from the specified number of recent days,
    ordered by creation date (most recent first).

    Args:
        days: Number of days to look back (1-90)
        limit: Maximum number of entries to return (1-50)
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of recent journal entries
    """
    entries = JournalService.get_recent_entries(
        db=db, user_id=current_user["uid"], days=days, limit=limit
    )
    return entries


@router.get("/search", response_model=list[JournalEntry])
def search_journal_entries(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search journal entries by content

    Performs case-insensitive search in journal entry content.
    Results are ordered by creation date (most recent first).

    Args:
        q: Search term (minimum 1 character)
        limit: Maximum number of results (1-50)
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of matching journal entries
    """
    entries = JournalService.search_entries(
        db=db, user_id=current_user["uid"], search_term=q, limit=limit
    )
    return entries


@router.get("/statistics")
def get_journal_statistics(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Get statistics about user's journal entries

    Provides insights into journaling habits and entry distribution.
    Useful for analytics and user dashboards.

    Args:
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Dictionary with journal entry statistics
    """
    stats = JournalService.get_entry_statistics(db, current_user["uid"])
    return stats


@router.get("/for/{parent_type}/{parent_id}", response_model=list[JournalEntry])
def get_journal_entries_for_parent(
    parent_type: str,
    parent_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get all journal entries associated with a specific parent entity

    Retrieves all journal entries linked to a project, goal, or task.
    Useful for displaying contextual notes in entity detail views.

    Args:
        parent_type: Type of parent entity ('project', 'goal', or 'task')
        parent_id: ID of the parent entity
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of journal entries associated with the parent entity

    Raises:
        400: If parent_type is invalid
    """
    if parent_type not in ["project", "goal", "task"]:
        raise HTTPException(
            status_code=400, detail="parent_type must be 'project', 'goal', or 'task'"
        )

    try:
        entries = JournalService.get_entries_for_parent(
            db=db,
            user_id=current_user["uid"],
            parent_type=parent_type,
            parent_id=parent_id,
        )
        return entries
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{entry_id}", response_model=JournalEntry)
def get_journal_entry(
    entry_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Get a specific journal entry by ID

    Retrieves a single journal entry with all associated entity details.
    Only the owner of the entry can access it.

    Args:
        entry_id: ID of the journal entry
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Journal entry details

    Raises:
        404: If entry not found or access denied
    """
    entry = JournalService.get_entry(db, current_user["uid"], entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return entry


@router.put("/{entry_id}", response_model=JournalEntry)
def update_journal_entry(
    entry_id: int,
    entry_data: JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update a journal entry

    Updates the content of an existing journal entry. The version number
    is automatically incremented for synchronization purposes.
    Only the owner of the entry can update it.

    Args:
        entry_id: ID of the journal entry to update
        entry_data: Updated entry data
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Updated journal entry

    Raises:
        404: If entry not found or access denied
        422: If validation fails
    """
    entry = JournalService.update_entry(db, current_user["uid"], entry_id, entry_data)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_journal_entry(
    entry_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Delete a journal entry

    Permanently removes a journal entry from the system.
    Only the owner of the entry can delete it.

    Args:
        entry_id: ID of the journal entry to delete
        db: Database session
        current_user: Currently authenticated user

    Raises:
        404: If entry not found or access denied
    """
    success = JournalService.delete_entry(db, current_user["uid"], entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Journal entry not found")
