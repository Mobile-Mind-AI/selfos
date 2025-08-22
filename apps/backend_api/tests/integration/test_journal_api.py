"""Integration tests for Journal API endpoints."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from main import app
from models import Goal, JournalEntry, LifeArea, Project, Task, User


class TestJournalAPI:
    """Test suite for Journal API endpoints"""

    @pytest.fixture(autouse=True)
    def setup_method(self, isolated_test_setup):
        """Set up test fixtures and authentication mock"""
        setup = isolated_test_setup
        self.db = setup["session_local"]()
        self.client = TestClient(app)

        # Check if test user already exists from isolated_test_setup
        self.test_user = self.db.query(User).filter(User.uid == "test_user_123").first()
        if not self.test_user:
            # Create test user with consistent UID
            self.test_user = User(uid="test_user_123", email="testuser@example.com")
            self.db.add(self.test_user)

        # Create test life area
        self.life_area = LifeArea(
            user_id=self.test_user.uid,
            name="Test Life Area",
            description="Test life area for journal tests",
        )
        self.db.add(self.life_area)
        self.db.flush()  # Get ID without committing

        # Create test project
        self.project = Project(
            user_id=self.test_user.uid,
            life_area_id=self.life_area.id,
            title="Test Project",
            description="Test project for journal tests",
        )
        self.db.add(self.project)
        self.db.flush()  # Get ID without committing

        # Create test goal
        self.goal = Goal(
            user_id=self.test_user.uid,
            life_area_id=self.life_area.id,
            project_id=self.project.id,
            title="Test Goal",
            description="Test goal for journal tests",
        )
        self.db.add(self.goal)
        self.db.flush()  # Get ID without committing

        # Create test task
        self.task = Task(
            user_id=self.test_user.uid,
            life_area_id=self.life_area.id,
            project_id=self.project.id,
            goal_id=self.goal.id,
            title="Test Task",
            description="Test task for journal tests",
        )
        self.db.add(self.task)

        # Commit all changes
        self.db.commit()

        # Refresh objects to get updated IDs
        self.db.refresh(self.life_area)
        self.db.refresh(self.project)
        self.db.refresh(self.goal)
        self.db.refresh(self.task)

    def teardown_method(self):
        """Clean up after each test"""
        if hasattr(self, "db"):
            self.db.close()

    def test_create_journal_entry_success(self):
        """Test successful journal entry creation"""
        entry_data = {
            "content": "This is my first journal entry!",
            "project_id": self.project.id,
            "goal_id": self.goal.id,
            "task_id": self.task.id,
        }

        response = self.client.post("/api/journal/", json=entry_data)

        assert response.status_code == 201
        data = response.json()

        assert data["content"] == entry_data["content"]
        assert data["project_id"] == self.project.id
        assert data["goal_id"] == self.goal.id
        assert data["task_id"] == self.task.id
        assert data["user_id"] == self.test_user.uid
        assert data["version"] == 1
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_journal_entry_standalone(self):
        """Test creating standalone journal entry"""
        entry_data = {"content": "This is a standalone journal entry"}

        response = self.client.post("/api/journal/", json=entry_data)

        assert response.status_code == 201
        data = response.json()

        assert data["content"] == entry_data["content"]
        assert data["project_id"] is None
        assert data["goal_id"] is None
        assert data["task_id"] is None
        assert data["user_id"] == self.test_user.uid

    def test_create_journal_entry_invalid_project(self):
        """Test journal entry creation with invalid project ID"""
        entry_data = {
            "content": "Test content",
            "project_id": 99999,  # Non-existent project
        }

        response = self.client.post("/api/journal/", json=entry_data)

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_create_journal_entry_invalid_content(self):
        """Test journal entry creation with invalid content"""
        entry_data = {"content": ""}  # Empty content should fail validation

        response = self.client.post("/api/journal/", json=entry_data)

        assert response.status_code == 422

    def test_get_journal_entries_empty(self):
        """Test getting journal entries when none exist"""
        response = self.client.get("/api/journal/")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_journal_entries_with_data(self):
        """Test getting journal entries when data exists"""
        # Create test entries
        entries = [
            JournalEntry(
                user_id=self.test_user.uid,
                content="First journal entry",
                project_id=self.project.id,
            ),
            JournalEntry(
                user_id=self.test_user.uid,
                content="Second journal entry",
                goal_id=self.goal.id,
            ),
            JournalEntry(user_id=self.test_user.uid, content="Third journal entry"),
        ]

        for entry in entries:
            self.db.add(entry)
        self.db.commit()

        response = self.client.get("/api/journal/")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3
        assert data[0]["content"] == "Third journal entry"  # Most recent first
        assert data[1]["content"] == "Second journal entry"
        assert data[2]["content"] == "First journal entry"

    def test_get_journal_entries_with_filters(self):
        """Test getting journal entries with various filters"""
        # Create entries with different associations
        project_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Project-related entry",
            project_id=self.project.id,
        )
        goal_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Goal-related entry",
            goal_id=self.goal.id,
        )
        task_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Task-related entry",
            task_id=self.task.id,
        )

        for entry in [project_entry, goal_entry, task_entry]:
            self.db.add(entry)
        self.db.commit()

        # Test project filter
        response = self.client.get(f"/api/journal/?project_id={self.project.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Project-related entry"

        # Test goal filter
        response = self.client.get(f"/api/journal/?goal_id={self.goal.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Goal-related entry"

        # Test task filter
        response = self.client.get(f"/api/journal/?task_id={self.task.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Task-related entry"

    def test_get_journal_entries_with_search(self):
        """Test getting journal entries with content search"""
        # Create entries with different content
        entries = [
            JournalEntry(
                user_id=self.test_user.uid,
                content="This entry contains python programming notes",
            ),
            JournalEntry(
                user_id=self.test_user.uid, content="Daily reflection on my goals"
            ),
            JournalEntry(
                user_id=self.test_user.uid,
                content="Python is a great programming language",
            ),
        ]

        for entry in entries:
            self.db.add(entry)
        self.db.commit()

        # Search for entries containing "python"
        response = self.client.get("/api/journal/?search=python")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        for entry in data:
            assert "python" in entry["content"].lower()

    def test_get_journal_entries_with_pagination(self):
        """Test getting journal entries with pagination"""
        # Create multiple entries
        for i in range(15):
            entry = JournalEntry(
                user_id=self.test_user.uid, content=f"Journal entry number {i+1}"
            )
            self.db.add(entry)
        self.db.commit()

        # Test first page
        response = self.client.get("/api/journal/?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # Test second page
        response = self.client.get("/api/journal/?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # Test third page
        response = self.client.get("/api/journal/?limit=5&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_get_journal_entry_count(self):
        """Test getting journal entry count"""
        # Initially should be 0
        response = self.client.get("/api/journal/count/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

        # Add some entries
        for i in range(3):
            entry = JournalEntry(user_id=self.test_user.uid, content=f"Entry {i+1}")
            self.db.add(entry)
        self.db.commit()

        # Should now be 3
        response = self.client.get("/api/journal/count/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_get_journal_entry_count_with_filters(self):
        """Test getting journal entry count with filters"""
        # Create entries with different associations
        project_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Project entry",
            project_id=self.project.id,
        )
        goal_entry = JournalEntry(
            user_id=self.test_user.uid, content="Goal entry", goal_id=self.goal.id
        )
        standalone_entry = JournalEntry(
            user_id=self.test_user.uid, content="Standalone entry"
        )

        for entry in [project_entry, goal_entry, standalone_entry]:
            self.db.add(entry)
        self.db.commit()

        # Test project filter count
        response = self.client.get(f"/api/journal/count?project_id={self.project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

        # Test total count
        response = self.client.get("/api/journal/count/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_get_recent_journal_entries(self):
        """Test getting recent journal entries"""
        # Create entries with different dates
        old_date = datetime.utcnow() - timedelta(days=10)
        recent_date = datetime.utcnow() - timedelta(days=2)

        old_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Old entry",
            created_at=old_date,
            entry_date=old_date,
        )
        recent_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Recent entry",
            created_at=recent_date,
            entry_date=recent_date,
        )

        self.db.add(old_entry)
        self.db.add(recent_entry)
        self.db.commit()

        # Get recent entries (default 7 days)
        response = self.client.get("/api/journal/recent/")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1  # Only the recent entry should be included
        assert data[0]["content"] == "Recent entry"

        # Get recent entries with longer period
        response = self.client.get("/api/journal/recent?days=15")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2  # Both entries should be included

    def test_search_journal_entries(self):
        """Test searching journal entries"""
        # Create entries with searchable content
        entries = [
            JournalEntry(
                user_id=self.test_user.uid,
                content="Today I learned about machine learning algorithms",
            ),
            JournalEntry(
                user_id=self.test_user.uid,
                content="Reflection on my daily routine and habits",
            ),
            JournalEntry(
                user_id=self.test_user.uid,
                content="Deep learning is a subset of machine learning",
            ),
        ]

        for entry in entries:
            self.db.add(entry)
        self.db.commit()

        # Search for "machine learning"
        response = self.client.get("/api/journal/search?q=machine learning")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        for entry in data:
            assert "machine learning" in entry["content"].lower()

    def test_get_journal_statistics(self):
        """Test getting journal entry statistics"""
        # Create entries with different associations
        project_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Project-related entry with some content",
            project_id=self.project.id,
        )
        goal_entry = JournalEntry(
            user_id=self.test_user.uid, content="Goal entry", goal_id=self.goal.id
        )
        task_entry = JournalEntry(
            user_id=self.test_user.uid, content="Task entry", task_id=self.task.id
        )
        standalone_entry = JournalEntry(
            user_id=self.test_user.uid, content="Standalone entry"
        )

        for entry in [project_entry, goal_entry, task_entry, standalone_entry]:
            self.db.add(entry)
        self.db.commit()

        response = self.client.get("/api/journal/statistics/")
        assert response.status_code == 200
        data = response.json()

        assert data["total_entries"] == 4
        assert data["entries_with_project"] == 1
        assert data["entries_with_goal"] == 1
        assert data["entries_with_task"] == 1
        assert data["standalone_entries"] == 1
        assert data["recent_entries_30d"] == 4
        assert data["average_content_length"] > 0
        assert data["first_entry_date"] is not None
        assert data["last_entry_date"] is not None

    def test_get_journal_entries_for_parent(self):
        """Test getting journal entries for specific parent entities"""
        # Create entries for different parents
        project_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Project notes",
            project_id=self.project.id,
        )
        goal_entry = JournalEntry(
            user_id=self.test_user.uid, content="Goal progress", goal_id=self.goal.id
        )
        task_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Task completion notes",
            task_id=self.task.id,
        )

        for entry in [project_entry, goal_entry, task_entry]:
            self.db.add(entry)
        self.db.commit()

        # Test getting entries for project
        response = self.client.get(f"/api/journal/for/project/{self.project.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Project notes"

        # Test getting entries for goal
        response = self.client.get(f"/api/journal/for/goal/{self.goal.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Goal progress"

        # Test getting entries for task
        response = self.client.get(f"/api/journal/for/task/{self.task.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Task completion notes"

    def test_get_journal_entries_for_parent_invalid_type(self):
        """Test getting journal entries with invalid parent type"""
        response = self.client.get("/api/journal/for/invalid/1/")
        assert response.status_code == 400
        assert "parent_type must be" in response.json()["detail"]

    def test_get_journal_entry_by_id(self):
        """Test getting specific journal entry by ID"""
        # Create a journal entry
        entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Specific journal entry",
            project_id=self.project.id,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        response = self.client.get(f"/api/journal/{entry.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == entry.id
        assert data["content"] == "Specific journal entry"
        assert data["project_id"] == self.project.id
        assert data["user_id"] == self.test_user.uid

    def test_get_journal_entry_not_found(self):
        """Test getting journal entry that doesn't exist"""
        response = self.client.get("/api/journal/99999/")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_journal_entry(self):
        """Test updating journal entry"""
        # Create a journal entry
        entry = JournalEntry(
            user_id=self.test_user.uid, content="Original content", version=1
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        # Update the entry
        update_data = {"content": "Updated content"}
        response = self.client.put(f"/api/journal/{entry.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == entry.id
        assert data["content"] == "Updated content"
        assert data["version"] == 2  # Version should be incremented
        assert data["user_id"] == self.test_user.uid

    def test_update_journal_entry_not_found(self):
        """Test updating journal entry that doesn't exist"""
        update_data = {"content": "Updated content"}
        response = self.client.put("/api/journal/99999/", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_journal_entry(self):
        """Test deleting journal entry"""
        # Create a journal entry
        entry = JournalEntry(user_id=self.test_user.uid, content="Entry to be deleted")
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        entry_id = entry.id

        # Delete the entry
        response = self.client.delete(f"/api/journal/{entry_id}")
        assert response.status_code == 204

        # Verify it's deleted
        response = self.client.get(f"/api/journal/{entry_id}")
        assert response.status_code == 404

    def test_delete_journal_entry_not_found(self):
        """Test deleting journal entry that doesn't exist"""
        response = self.client.delete("/api/journal/99999/")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_journal_entry_validation(self):
        """Test journal entry content validation"""
        # Test empty content
        response = self.client.post("/api/journal/", json={"content": ""})
        assert response.status_code == 422

        # Test too long content (over 10000 characters)
        long_content = "x" * 10001
        response = self.client.post("/api/journal/", json={"content": long_content})
        assert response.status_code == 422

        # Test valid content
        response = self.client.post("/api/journal/", json={"content": "Valid content"})
        assert response.status_code == 201

    def test_journal_entry_date_filtering(self):
        """Test journal entry filtering by date range"""
        # Create entries with different dates
        old_date = datetime.utcnow() - timedelta(days=10)
        recent_date = datetime.utcnow() - timedelta(days=2)

        old_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Old entry",
            created_at=old_date,
            entry_date=old_date,
        )
        recent_entry = JournalEntry(
            user_id=self.test_user.uid,
            content="Recent entry",
            created_at=recent_date,
            entry_date=recent_date,
        )

        self.db.add(old_entry)
        self.db.add(recent_entry)
        self.db.commit()

        # Filter by start date
        start_date = (datetime.utcnow() - timedelta(days=5)).isoformat()
        response = self.client.get(f"/api/journal/?start_date={start_date}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Recent entry"

        # Filter by end date
        end_date = (datetime.utcnow() - timedelta(days=5)).isoformat()
        response = self.client.get(f"/api/journal/?end_date={end_date}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Old entry"
