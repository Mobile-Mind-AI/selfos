"""
Unit tests for Projects API endpoints.

Tests the complete project management functionality including CRUD operations,
progress tracking, and timeline features.
"""

import pytest
from datetime import datetime, timedelta
from models import User, Project, Goal, Task, LifeArea, MediaAttachment


@pytest.fixture
def db_session(isolated_test_setup):
    """Create a database session for project tests"""
    session = isolated_test_setup["session_local"]()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(uid="test_user_123", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_life_area(db_session, test_user):
    """Create a test life area."""
    life_area = LifeArea(
        user_id=test_user.uid,
        name="Work",
        weight=30,
        description="Professional development"
    )
    db_session.add(life_area)
    db_session.commit()
    db_session.refresh(life_area)
    return life_area


@pytest.fixture
def test_project(db_session, test_user, test_life_area):
    """Create a test project."""
    project = Project(
        user_id=test_user.uid,
        life_area_id=test_life_area.id,
        title="Test Project",
        description="A test project for unit testing",
        status="active",
        priority="high"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestProjectCRUD:
    """Test Project CRUD operations."""
    
    def test_create_project_success(self, client, db_session, test_user):
        """Test successful project creation."""
        project_data = {
            "title": "New Project",
            "description": "A brand new project",
            "priority": "medium",
            "status": "planning"
        }
        
        response = client.post("/api/projects/", json=project_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Project"
        assert data["description"] == "A brand new project"
        assert data["life_area_id"] is None
        assert data["priority"] == "medium"
        assert data["status"] == "planning"
        assert data["user_id"] == "test_user_123"
        assert data["life_area"] is None
        assert data["goals"] == []
        assert data["tasks"] == []
        
        # API response confirms project was created successfully
    
    def test_create_project_without_life_area(self, client, db_session, test_user):
        """Test creating project without life area."""
        project_data = {
            "title": "Standalone Project",
            "description": "Project without life area",
            "priority": "low"
        }
        
        response = client.post("/api/projects/", json=project_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Standalone Project"
        assert data["life_area_id"] is None
        assert data["life_area"] is None
    
    def test_create_project_invalid_life_area(self, client, db_session, test_user):
        """Test creating project with invalid life area."""
        project_data = {
            "title": "Invalid Project",
            "life_area_id": 999  # Non-existent life area
        }
        
        response = client.post("/api/projects/", json=project_data)
        
        assert response.status_code == 404
        assert "Life area not found" in response.json()["detail"]
    
    def test_create_project_validation_errors(self, client, db_session, test_user):
        """Test project creation with validation errors."""
        # Missing required title
        response = client.post("/api/projects/", json={})
        assert response.status_code == 422
        
        # Title too long
        project_data = {"title": "x" * 201}  # Exceeds 200 character limit
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 422
        
        # Invalid priority
        project_data = {"title": "Test", "priority": "invalid_priority"}
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == 422
    
    def test_list_projects_empty(self, client, db_session, test_user):
        """Test listing projects when none exist."""
        response = client.get("/api/projects/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_projects_with_data(self, client, db_session, test_user, test_project):
        """Test listing projects with existing data."""
        response = client.get("/api/projects/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Project"
        assert data[0]["id"] == test_project.id
    
    def test_list_projects_with_filters(self, client, db_session, test_user, test_life_area):
        """Test listing projects with various filters."""
        # Create projects with different statuses and priorities
        projects_data = [
            {"title": "Planning Project", "status": "planning", "priority": "low", "life_area_id": test_life_area.id},
            {"title": "Active Project", "status": "active", "priority": "high"},
            {"title": "Completed Project", "status": "completed", "priority": "medium"},
        ]
        
        for project_data in projects_data:
            client.post("/api/projects/", json=project_data)
        
        # Test status filter
        response = client.get("/api/projects/?status=planning")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Planning Project"
        
        # Test priority filter
        response = client.get("/api/projects/?priority=high")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Active Project"
        
        # Test life_area_id filter
        response = client.get(f"/api/projects/?life_area_id={test_life_area.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Planning Project"
        
        # Test pagination
        response = client.get("/api/projects/?limit=2&offset=0")
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        response = client.get("/api/projects/?limit=2&offset=2")
        assert response.status_code == 200
        assert len(response.json()) == 1
    
    def test_get_project_success(self, client, db_session, test_user, test_project):
        """Test getting a specific project."""
        response = client.get(f"/api/projects/{test_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["title"] == "Test Project"
        assert data["user_id"] == "test_user_123"
    
    def test_get_project_not_found(self, client, db_session, test_user):
        """Test getting non-existent project."""
        response = client.get("/api/projects/999")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    def test_update_project_success(self, client, db_session, test_user, test_project):
        """Test successful project update."""
        update_data = {
            "title": "Updated Project Title",
            "description": "Updated description",
            "status": "completed",
            "priority": "low",
            "progress": 100.0
        }
        
        response = client.put(f"/api/projects/{test_project.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Project Title"
        assert data["description"] == "Updated description"
        assert data["status"] == "completed"
        assert data["priority"] == "low"
        assert data["progress"] == 100.0
        
        # Verify in database
        db_session.refresh(test_project)
        assert test_project.title == "Updated Project Title"
        assert test_project.status == "completed"
    
    def test_update_project_not_found(self, client, db_session, test_user):
        """Test updating non-existent project."""
        update_data = {"title": "Updated Title"}
        response = client.put("/api/projects/999", json=update_data)
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    def test_delete_project_success(self, client, db_session, test_user, test_project):
        """Test successful project deletion."""
        project_id = test_project.id
        
        response = client.delete(f"/api/projects/{project_id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify deletion in database
        project = db_session.query(Project).filter(Project.id == project_id).first()
        assert project is None
    
    def test_delete_project_not_found(self, client, db_session, test_user):
        """Test deleting non-existent project."""
        response = client.delete("/api/projects/999")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]


class TestProjectProgress:
    """Test project progress tracking functionality."""
    
    def test_project_progress_empty(self, client, db_session, test_user, test_project):
        """Test progress calculation with no goals or tasks."""
        response = client.get(f"/api/projects/{test_project.id}/progress")
        
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == test_project.id
        assert data["overall_progress"] == 0
        assert data["goals"]["total"] == 0
        assert data["goals"]["completed"] == 0
        assert data["tasks"]["total"] == 0
        assert data["tasks"]["completed"] == 0
    
    def test_project_progress_with_goals_and_tasks(self, client, db_session, test_user, test_project):
        """Test progress calculation with goals and tasks."""
        # Create goals for the project
        goal1 = Goal(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Goal 1",
            status="completed"
        )
        goal2 = Goal(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Goal 2",
            status="in_progress"
        )
        
        # Create tasks for the project
        task1 = Task(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Task 1",
            status="completed"
        )
        task2 = Task(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Task 2",
            status="completed"
        )
        task3 = Task(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Task 3",
            status="in_progress"
        )
        
        db_session.add_all([goal1, goal2, task1, task2, task3])
        db_session.commit()
        
        response = client.get(f"/api/projects/{test_project.id}/progress")
        
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == test_project.id
        
        # Goals: 1/2 completed = 50%
        assert data["goals"]["total"] == 2
        assert data["goals"]["completed"] == 1
        assert data["goals"]["progress"] == 50.0
        
        # Tasks: 2/3 completed = 66.67%
        assert data["tasks"]["total"] == 3
        assert data["tasks"]["completed"] == 2
        assert data["tasks"]["in_progress"] == 1
        assert data["tasks"]["progress"] == 66.67
        
        # Overall: (50% * 0.6) + (66.67% * 0.4) = 56.67%
        expected_overall = (50.0 * 0.6) + (66.67 * 0.4)
        assert abs(data["overall_progress"] - expected_overall) < 0.1
    
    def test_project_progress_not_found(self, client, db_session, test_user):
        """Test progress for non-existent project."""
        response = client.get("/api/projects/999/progress")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]


class TestProjectTimeline:
    """Test project timeline functionality."""
    
    def test_project_timeline_empty(self, client, db_session, test_user, test_project):
        """Test timeline with only project creation event."""
        response = client.get(f"/api/projects/{test_project.id}/timeline")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "project_created"
        assert "Project 'Test Project' created" in data[0]["title"]
        assert data[0]["item_id"] == test_project.id
    
    def test_project_timeline_with_events(self, client, db_session, test_user, test_project):
        """Test timeline with multiple events."""
        # Create a goal
        goal = Goal(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Test Goal",
            status="completed",
            created_at=datetime.utcnow() + timedelta(hours=1),
            updated_at=datetime.utcnow() + timedelta(hours=2)
        )
        
        # Create a task
        task = Task(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Test Task",
            status="completed",
            created_at=datetime.utcnow() + timedelta(hours=3),
            updated_at=datetime.utcnow() + timedelta(hours=4)
        )
        
        db_session.add_all([goal, task])
        db_session.commit()
        
        response = client.get(f"/api/projects/{test_project.id}/timeline")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have: project_created, goal_created, task_created, task_completed
        assert len(data) == 4
        
        # Events should be sorted by date (newest first)
        event_types = [event["type"] for event in data]
        assert "task_completed" in event_types
        assert "task_created" in event_types
        assert "goal_created" in event_types
        assert "project_created" in event_types
        
        # Check task completion event
        task_completed_event = next(e for e in data if e["type"] == "task_completed")
        assert "Test Task" in task_completed_event["title"]
        assert "completed" in task_completed_event["title"]
    
    def test_project_timeline_not_found(self, client, db_session, test_user):
        """Test timeline for non-existent project."""
        response = client.get("/api/projects/999/timeline")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]


class TestProjectRelationships:
    """Test project relationships with goals, tasks, and media."""
    
    def test_project_with_goals(self, client, db_session, test_user, test_project):
        """Test project with associated goals."""
        # Create goals for the project
        goal1 = Goal(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Project Goal 1",
            description="First goal"
        )
        goal2 = Goal(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Project Goal 2",
            description="Second goal"
        )
        
        db_session.add_all([goal1, goal2])
        db_session.commit()
        
        response = client.get(f"/api/projects/{test_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["goals"]) == 2
        
        goal_titles = [goal["title"] for goal in data["goals"]]
        assert "Project Goal 1" in goal_titles
        assert "Project Goal 2" in goal_titles
    
    def test_project_with_tasks(self, client, db_session, test_user, test_project):
        """Test project with associated tasks."""
        # Create tasks for the project
        task1 = Task(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Project Task 1",
            description="First task"
        )
        task2 = Task(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Project Task 2",
            description="Second task"
        )
        
        db_session.add_all([task1, task2])
        db_session.commit()
        
        response = client.get(f"/api/projects/{test_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        
        task_titles = [task["title"] for task in data["tasks"]]
        assert "Project Task 1" in task_titles
        assert "Project Task 2" in task_titles
    
    def test_project_deletion_cascades(self, client, db_session, test_user, test_project):
        """Test that deleting a project also deletes associated goals and tasks."""
        # Create associated items
        goal = Goal(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Goal to be deleted"
        )
        task = Task(
            user_id=test_user.uid,
            project_id=test_project.id,
            title="Task to be deleted"
        )
        
        db_session.add_all([goal, task])
        db_session.commit()
        
        goal_id = goal.id
        task_id = task.id
        project_id = test_project.id
        
        # Delete the project
        response = client.delete(f"/api/projects/{project_id}")
        assert response.status_code == 200
        
        # Verify all associated items are deleted
        assert db_session.query(Project).filter(Project.id == project_id).first() is None
        assert db_session.query(Goal).filter(Goal.id == goal_id).first() is None
        assert db_session.query(Task).filter(Task.id == task_id).first() is None


class TestProjectSecurity:
    """Test project security and user isolation."""
    
    def test_user_cannot_access_other_users_projects(self, client, db_session):
        """Test that users can only access their own projects."""
        # Create another user and their project
        other_user = User(uid="other_user_456", email="other@example.com")
        db_session.add(other_user)
        db_session.commit()
        
        other_project = Project(
            user_id=other_user.uid,
            title="Other User's Project",
            description="Should not be accessible"
        )
        db_session.add(other_project)
        db_session.commit()
        
        # Current user (test_user_123) should not see other user's project
        response = client.get("/api/projects/")
        assert response.status_code == 200
        projects = response.json()
        
        # Should not find the other user's project
        project_titles = [p["title"] for p in projects]
        assert "Other User's Project" not in project_titles
        
        # Should not be able to access other user's project directly
        response = client.get(f"/api/projects/{other_project.id}")
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
        
        # Should not be able to update other user's project
        response = client.put(f"/api/projects/{other_project.id}", json={"title": "Hacked"})
        assert response.status_code == 404
        
        # Should not be able to delete other user's project
        response = client.delete(f"/api/projects/{other_project.id}")
        assert response.status_code == 404


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
