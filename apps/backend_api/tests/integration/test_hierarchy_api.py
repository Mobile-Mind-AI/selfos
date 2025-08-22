"""
Integration tests for Hierarchy API endpoints.

Tests complete workflows for hierarchical goals and projects,
using conftest.py fixtures for authentication and database setup.
"""

from fastapi.testclient import TestClient
from models import Goal, LifeArea, Project
from sqlalchemy.orm import Session


class TestHierarchyAPI:
    """Integration tests for hierarchy API endpoints."""

    def create_test_goal(self, db: Session, title: str, parent_id: int = None) -> Goal:
        """Create a real goal object in the database."""
        # Ensure we have a life area
        life_area = db.query(LifeArea).filter(LifeArea.user_id == "system").first()
        if not life_area:
            life_area = LifeArea(
                user_id="system",
                name="Personal Growth",
                description="Personal Growth description",
            )
            db.add(life_area)
            db.commit()
            db.refresh(life_area)

        goal = Goal(
            title=title,
            description=f"Description for {title}",
            status="todo",
            progress=0,
            user_id="test_user_123",  # Matches conftest.py mock user
            life_area_id=life_area.id,
            parent_id=parent_id,
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal

    def create_test_project(
        self, db: Session, title: str, parent_id: int = None
    ) -> Project:
        """Create a real project object in the database."""
        # Ensure we have a life area
        life_area = db.query(LifeArea).filter(LifeArea.user_id == "system").first()
        if not life_area:
            life_area = LifeArea(
                user_id="system",
                name="Personal Growth",
                description="Personal Growth description",
            )
            db.add(life_area)
            db.commit()
            db.refresh(life_area)

        project = Project(
            title=title,
            description=f"Description for {title}",
            status="planning",
            progress=0,
            priority="medium",
            user_id="test_user_123",  # Matches conftest.py mock user
            life_area_id=life_area.id,
            parent_id=parent_id,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def test_get_root_goals_api(self, client: TestClient, db: Session):
        """Test GET /api/goals/roots API endpoint."""
        # Clean slate - remove any existing goals to avoid interference from other tests
        db.query(Goal).filter(Goal.user_id == "test_user_123").delete()
        db.commit()

        # Create real test data
        goal1 = self.create_test_goal(db, "Career Growth")
        goal2 = self.create_test_goal(db, "Health Improvement")

        # Make API request
        response = client.get("/api/goals/roots/")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        titles = [goal["title"] for goal in data]
        assert "Career Growth" in titles
        assert "Health Improvement" in titles

    def test_get_goal_children_api(self, client: TestClient, db: Session):
        """Test GET /api/goals/{goal_id}/children API endpoint."""
        # Clean slate
        db.query(Goal).filter(Goal.user_id == "test_user_123").delete()
        db.commit()

        # Create parent goal
        parent_goal = self.create_test_goal(db, "Parent Goal")

        # Create child goals
        child1 = self.create_test_goal(db, "Child Goal 1", parent_goal.id)
        child2 = self.create_test_goal(db, "Child Goal 2", parent_goal.id)

        # Make API request
        response = client.get(f"/api/goals/{parent_goal.id}/children")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        titles = [goal["title"] for goal in data]
        assert "Child Goal 1" in titles
        assert "Child Goal 2" in titles

    def test_get_goal_children_not_found(self, client: TestClient, db: Session):
        """Test GET /api/goals/{goal_id}/children with non-existent goal."""
        goal_id = 999

        # Make API request
        response = client.get(f"/api/goals/{goal_id}/children")

        # Verify error response
        assert response.status_code == 404
        assert "Goal not found" in response.json()["detail"]

    def test_get_goal_tree_api(self, client: TestClient, db: Session):
        """Test GET /api/goals/tree API endpoint."""
        # Clean slate
        db.query(Goal).filter(Goal.user_id == "test_user_123").delete()
        db.commit()

        # Create hierarchical structure
        root_goal = self.create_test_goal(db, "Career")
        child_goal = self.create_test_goal(db, "Learn Python", root_goal.id)

        another_root = self.create_test_goal(db, "Health")

        # Make API request
        response = client.get("/api/goals/tree/")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Find Career goal in response
        career_goal = next((g for g in data if g["title"] == "Career"), None)
        assert career_goal is not None
        assert len(career_goal["children"]) == 1
        assert career_goal["children"][0]["title"] == "Learn Python"

        # Find Health goal in response
        health_goal = next((g for g in data if g["title"] == "Health"), None)
        assert health_goal is not None
        assert len(health_goal["children"]) == 0

    def test_move_goal_api_success(self, client: TestClient, db: Session):
        """Test PUT /api/goals/{goal_id}/move API endpoint success case."""
        # Clean slate
        db.query(Goal).filter(Goal.user_id == "test_user_123").delete()
        db.commit()

        # Create test goals
        parent_goal = self.create_test_goal(db, "Parent Goal")
        child_goal = self.create_test_goal(db, "Child Goal")

        # Make API request to move child under parent
        response = client.put(
            f"/api/goals/{child_goal.id}/move", json={"parent_id": parent_goal.id}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == child_goal.id
        assert data["parent_id"] == parent_goal.id

        # Verify database was updated
        db.refresh(child_goal)
        assert child_goal.parent_id == parent_goal.id

    def test_move_goal_api_cycle_error(self, client: TestClient, db: Session):
        """Test PUT /api/goals/{goal_id}/move API endpoint with cycle error."""
        # Clean slate
        db.query(Goal).filter(Goal.user_id == "test_user_123").delete()
        db.commit()

        # Create parent-child relationship
        parent_goal = self.create_test_goal(db, "Parent Goal")
        child_goal = self.create_test_goal(db, "Child Goal", parent_goal.id)

        # Try to move parent under child (would create cycle)
        response = client.put(
            f"/api/goals/{parent_goal.id}/move", json={"parent_id": child_goal.id}
        )

        # Verify error response
        assert response.status_code == 400
        assert (
            "Moving goal would create a cycle in hierarchy" in response.json()["detail"]
        )

    def test_move_goal_api_not_found(self, client: TestClient, db: Session):
        """Test PUT /api/goals/{goal_id}/move API endpoint with non-existent goal."""
        goal_id = 999
        parent_goal = self.create_test_goal(db, "Parent Goal")

        # Make API request
        response = client.put(
            f"/api/goals/{goal_id}/move", json={"parent_id": parent_goal.id}
        )

        # Verify error response
        assert response.status_code == 404
        assert "Goal not found" in response.json()["detail"]

    def test_get_root_projects_api(self, client: TestClient, db: Session):
        """Test GET /api/projects/roots API endpoint."""
        # Clean slate - remove existing projects to avoid interference
        db.query(Project).filter(Project.user_id == "test_user_123").delete()
        db.commit()

        # Create real test data
        project1 = self.create_test_project(db, "Work Projects")
        project2 = self.create_test_project(db, "Personal Projects")

        # Make API request
        response = client.get("/api/projects/roots/")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        titles = [project["title"] for project in data]
        assert "Work Projects" in titles
        assert "Personal Projects" in titles

    def test_get_project_tree_api(self, client: TestClient, db: Session):
        """Test GET /api/projects/tree API endpoint."""
        # Clean slate
        db.query(Project).filter(Project.user_id == "test_user_123").delete()
        db.commit()

        # Create hierarchical structure
        root_project = self.create_test_project(db, "Work")
        child_project = self.create_test_project(db, "New Website", root_project.id)

        # Make API request
        response = client.get("/api/projects/tree/")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        work_project = data[0]
        assert work_project["title"] == "Work"
        assert len(work_project["children"]) == 1
        assert work_project["children"][0]["title"] == "New Website"

    def test_move_project_api_success(self, client: TestClient, db: Session):
        """Test PUT /api/projects/{project_id}/move API endpoint success case."""
        # Clean slate
        db.query(Project).filter(Project.user_id == "test_user_123").delete()
        db.commit()

        # Create test projects
        parent_project = self.create_test_project(db, "Parent Project")
        child_project = self.create_test_project(db, "Child Project")

        # Make API request to move child under parent
        response = client.put(
            f"/api/projects/{child_project.id}/move",
            json={"parent_id": parent_project.id},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == child_project.id
        assert data["parent_id"] == parent_project.id

        # Verify database was updated
        db.refresh(child_project)
        assert child_project.parent_id == parent_project.id

    def test_move_goal_to_root_level_api(self, client: TestClient, db: Session):
        """Test moving goal to root level (parent_id = None)."""
        # Clean slate
        db.query(Goal).filter(Goal.user_id == "test_user_123").delete()
        db.commit()

        # Create parent-child relationship
        parent_goal = self.create_test_goal(db, "Parent Goal")
        child_goal = self.create_test_goal(db, "Child Goal", parent_goal.id)

        # Move child to root level
        response = client.put(
            f"/api/goals/{child_goal.id}/move", json={"parent_id": None}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == child_goal.id
        assert data["parent_id"] is None

        # Verify database was updated
        db.refresh(child_goal)
        assert child_goal.parent_id is None

    def test_hierarchy_api_input_validation(self, client: TestClient, db: Session):
        """Test input validation for hierarchy API endpoints."""
        # Test invalid goal ID (non-numeric)
        response = client.get("/api/goals/invalid/children/")
        assert response.status_code == 422

        # Test invalid project ID (non-numeric)
        response = client.get("/api/projects/invalid/descendants/")
        assert response.status_code == 422

        # Test valid move request with None parent_id (moves to root)
        goal = self.create_test_goal(db, "Test Goal")
        response = client.put(f"/api/goals/{goal.id}/move", json={"parent_id": None})
        assert response.status_code == 200
        assert response.json()["parent_id"] is None

        # Test invalid move request (wrong data type)
        response = client.put(
            f"/api/goals/{goal.id}/move", json={"parent_id": "invalid"}
        )
        assert response.status_code == 422

    def test_hierarchy_with_deep_nesting(self, client: TestClient, db: Session):
        """Test API with deeply nested hierarchies."""
        # Clean slate
        db.query(Goal).filter(Goal.user_id == "test_user_123").delete()
        db.commit()

        # Create a deep hierarchy (5 levels)
        current_parent = None
        goals = []

        for i in range(5):
            goal = self.create_test_goal(db, f"Level {i+1} Goal", current_parent)
            goals.append(goal)
            current_parent = goal.id

        # Test tree endpoint with deep nesting
        response = client.get("/api/goals/tree/")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1  # Should have one root

        # Navigate down the tree to verify structure
        current_level = data[0]
        for i in range(4):  # 4 levels of children
            assert current_level["title"] == f"Level {i+1} Goal"
            assert len(current_level["children"]) == 1
            current_level = current_level["children"][0]

        # Last level should have no children
        assert current_level["title"] == "Level 5 Goal"
        assert len(current_level["children"]) == 0

    def test_complete_hierarchy_workflow(self, client: TestClient, db: Session):
        """Test complete workflow: create goals/projects, organize in hierarchy, navigate tree."""
        # Clean slate
        db.query(Goal).filter(Goal.user_id == "test_user_123").delete()
        db.commit()

        # Step 1: Create some root goals
        career_goal = self.create_test_goal(db, "Career Development")
        health_goal = self.create_test_goal(db, "Health & Fitness")

        # Step 2: Add sub-goals
        python_goal = self.create_test_goal(db, "Learn Python", career_goal.id)
        exercise_goal = self.create_test_goal(db, "Regular Exercise", health_goal.id)

        # Step 3: Add sub-sub-goals
        django_goal = self.create_test_goal(db, "Learn Django", python_goal.id)

        # Step 4: Test navigation through API

        # Get root goals
        response = client.get("/api/goals/roots/")
        assert response.status_code == 200
        roots = response.json()
        assert len(roots) == 2

        # Get career goal children
        response = client.get(f"/api/goals/{career_goal.id}/children")
        assert response.status_code == 200
        career_children = response.json()
        assert len(career_children) == 1
        assert career_children[0]["title"] == "Learn Python"

        # Get full tree
        response = client.get("/api/goals/tree/")
        assert response.status_code == 200
        tree = response.json()
        assert len(tree) == 2

        # Find career branch and verify structure
        career_branch = next(
            (g for g in tree if g["title"] == "Career Development"), None
        )
        assert career_branch is not None
        assert len(career_branch["children"]) == 1

        python_branch = career_branch["children"][0]
        assert python_branch["title"] == "Learn Python"
        assert len(python_branch["children"]) == 1
        assert python_branch["children"][0]["title"] == "Learn Django"

        # Step 5: Test reorganization - move Django to be direct child of Career
        response = client.put(
            f"/api/goals/{django_goal.id}/move", json={"parent_id": career_goal.id}
        )
        assert response.status_code == 200

        # Verify the move worked
        response = client.get(f"/api/goals/{career_goal.id}/children")
        career_children = response.json()
        titles = [child["title"] for child in career_children]
        assert "Learn Python" in titles
        assert "Learn Django" in titles
        assert len(career_children) == 2

    def test_project_hierarchy_workflow(self, client: TestClient, db: Session):
        """Test project hierarchy workflow."""
        # Clean slate
        db.query(Project).filter(Project.user_id == "test_user_123").delete()
        db.commit()

        # Create project hierarchy
        work_project = self.create_test_project(db, "Work Projects")
        website_project = self.create_test_project(
            db, "Company Website", work_project.id
        )

        # Test project endpoints
        response = client.get("/api/projects/roots/")
        assert response.status_code == 200
        assert len(response.json()) == 1

        response = client.get("/api/projects/tree/")
        assert response.status_code == 200
        tree = response.json()
        assert len(tree) == 1
        assert tree[0]["title"] == "Work Projects"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["title"] == "Company Website"

        # Test project move
        personal_project = self.create_test_project(db, "Personal Project")
        response = client.put(
            f"/api/projects/{personal_project.id}/move",
            json={"parent_id": work_project.id},
        )
        assert response.status_code == 200

        # Verify move
        response = client.get("/api/projects/tree/")
        tree = response.json()
        work_children = tree[0]["children"]
        titles = [child["title"] for child in work_children]
        assert "Company Website" in titles
        assert "Personal Project" in titles
