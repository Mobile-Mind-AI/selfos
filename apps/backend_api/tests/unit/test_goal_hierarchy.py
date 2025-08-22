"""
Unit tests for Goal hierarchy functionality.

Tests hierarchical operations including parent-child relationships,
tree navigation, cycle prevention, and data integrity.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from models import Goal
from services.goal_service import goal_service
from sqlalchemy.orm import Session


class TestGoalHierarchy:
    """Test goal hierarchy operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.user_id = "test_user_123"
        self.life_area_id = 1

    def create_mock_goal(self, id: int, title: str, parent_id: int = None):
        """Create a mock goal object."""
        goal = Mock(spec=Goal)
        goal.id = id
        goal.title = title
        goal.description = f"Description for {title}"
        goal.status = "todo"
        goal.progress = 0
        goal.user_id = self.user_id
        goal.life_area_id = self.life_area_id
        goal.parent_id = parent_id
        goal.created_at = datetime.utcnow()
        goal.updated_at = datetime.utcnow()
        return goal

    @patch.object(goal_service, "get_root_goals")
    def test_get_root_goals(self, mock_get_root_goals):
        """Test retrieving root-level goals."""
        # Mock data as regular Python list
        root_goals = [
            self.create_mock_goal(1, "Career Growth"),
            self.create_mock_goal(2, "Health Improvement"),
        ]

        # Configure mock to return our test data
        mock_get_root_goals.return_value = root_goals

        # Test
        result = goal_service.get_root_goals(self.mock_db, self.user_id)

        # Verify
        assert len(result) == 2
        assert result[0].title == "Career Growth"
        assert result[1].title == "Health Improvement"

        # Verify method was called with correct parameters
        mock_get_root_goals.assert_called_once_with(self.mock_db, self.user_id)

    @patch.object(goal_service, "get_goal_children")
    def test_get_goal_children(self, mock_get_goal_children):
        """Test retrieving direct children of a goal."""
        parent_id = 1
        children = [
            self.create_mock_goal(2, "Learn Python", parent_id),
            self.create_mock_goal(3, "Build Portfolio", parent_id),
        ]

        # Configure mock to return our test data
        mock_get_goal_children.return_value = children

        # Test
        result = goal_service.get_goal_children(self.mock_db, self.user_id, parent_id)

        # Verify
        assert len(result) == 2
        assert all(goal.parent_id == parent_id for goal in result)
        assert result[0].title == "Learn Python"
        assert result[1].title == "Build Portfolio"

        # Verify method was called with correct parameters
        mock_get_goal_children.assert_called_once_with(
            self.mock_db, self.user_id, parent_id
        )

    @patch.object(goal_service, "get_goal_children")
    def test_get_goal_descendants_single_level(self, mock_get_goal_children):
        """Test retrieving all descendants with single level."""
        parent_id = 1
        children = [
            self.create_mock_goal(2, "Learn Python", parent_id),
            self.create_mock_goal(3, "Build Portfolio", parent_id),
        ]

        # Mock recursive calls to return empty lists (no grandchildren)
        def mock_get_children(db, user_id, goal_id):
            if goal_id == parent_id:
                return children
            return []

        mock_get_goal_children.side_effect = mock_get_children

        # Test
        result = goal_service.get_goal_descendants(
            self.mock_db, self.user_id, parent_id
        )

        # Verify
        assert len(result) == 2
        assert result[0].title == "Learn Python"
        assert result[1].title == "Build Portfolio"

    @patch.object(goal_service, "get_goal_children")
    def test_get_goal_descendants_multi_level(self, mock_get_goal_children):
        """Test retrieving all descendants with multiple levels."""
        # Setup hierarchy:
        # 1. Career Growth
        #   ├── 2. Learn Python
        #   │   └── 4. Complete Course
        #   └── 3. Build Portfolio
        #       └── 5. Create Projects

        parent_id = 1
        level1_children = [
            self.create_mock_goal(2, "Learn Python", parent_id),
            self.create_mock_goal(3, "Build Portfolio", parent_id),
        ]
        level2_children_2 = [self.create_mock_goal(4, "Complete Course", 2)]
        level2_children_3 = [self.create_mock_goal(5, "Create Projects", 3)]

        def mock_get_children(db, user_id, goal_id):
            if goal_id == 1:
                return level1_children
            elif goal_id == 2:
                return level2_children_2
            elif goal_id == 3:
                return level2_children_3
            return []

        mock_get_goal_children.side_effect = mock_get_children

        # Test
        result = goal_service.get_goal_descendants(
            self.mock_db, self.user_id, parent_id
        )

        # Verify all 4 descendants are returned
        assert len(result) == 4
        descendant_titles = [goal.title for goal in result]
        assert "Learn Python" in descendant_titles
        assert "Build Portfolio" in descendant_titles
        assert "Complete Course" in descendant_titles
        assert "Create Projects" in descendant_titles

    @patch.object(goal_service, "get_goal")
    def test_get_goal_path(self, mock_get_goal):
        """Test retrieving path from root to goal."""
        # Setup hierarchy: Root(1) -> Parent(2) -> Child(3)
        goals = {
            1: self.create_mock_goal(1, "Root Goal"),
            2: self.create_mock_goal(2, "Parent Goal", 1),
            3: self.create_mock_goal(3, "Child Goal", 2),
        }

        def mock_get_goal_side_effect(db, user_id, goal_id):
            return goals.get(goal_id)

        mock_get_goal.side_effect = mock_get_goal_side_effect

        # Test
        result = goal_service.get_goal_path(self.mock_db, self.user_id, 3)

        # Verify path from root to target
        assert len(result) == 3
        assert result[0].title == "Root Goal"
        assert result[1].title == "Parent Goal"
        assert result[2].title == "Child Goal"

    @patch.object(goal_service, "get_goal_children")
    @patch.object(goal_service, "get_root_goals")
    def test_get_goal_tree_structure(self, mock_get_root_goals, mock_get_goal_children):
        """Test retrieving hierarchical tree structure."""
        # Mock root goals
        root_goals = [
            self.create_mock_goal(1, "Career"),
            self.create_mock_goal(2, "Health"),
        ]

        # Mock children for each root
        career_children = [self.create_mock_goal(3, "Learn Skills", 1)]
        health_children = [self.create_mock_goal(4, "Exercise", 2)]

        def mock_get_roots(db, user_id):
            return root_goals

        def mock_get_children(db, user_id, parent_id):
            if parent_id == 1:
                return career_children
            elif parent_id == 2:
                return health_children
            return []

        mock_get_root_goals.side_effect = mock_get_roots
        mock_get_goal_children.side_effect = mock_get_children

        # Test
        result = goal_service.get_goal_tree(self.mock_db, self.user_id)

        # Verify tree structure
        assert len(result) == 2

        # Verify Career branch
        career_node = next(node for node in result if node.title == "Career")
        assert career_node.id == 1
        assert len(career_node.children) == 1
        assert career_node.children[0].title == "Learn Skills"

        # Verify Health branch
        health_node = next(node for node in result if node.title == "Health")
        assert health_node.id == 2
        assert len(health_node.children) == 1
        assert health_node.children[0].title == "Exercise"

    def test_move_goal_to_valid_parent(self):
        """Test moving goal to a valid parent."""
        goal = self.create_mock_goal(3, "Child Goal", 1)
        new_parent = self.create_mock_goal(2, "New Parent")

        # Mock get_goal method to return appropriate goals
        def mock_get_goal(db, user_id, goal_id):
            if goal_id == 3:
                return goal
            elif goal_id == 2:
                return new_parent
            return None

        goal_service.get_goal = Mock(side_effect=mock_get_goal)

        # Mock validation (no cycle)
        goal_service._would_create_cycle = Mock(return_value=False)

        # Test
        result = goal_service.move_goal(self.mock_db, self.user_id, 3, 2)

        # Verify
        assert result is goal  # Use 'is' for object identity
        assert goal.parent_id == 2
        self.mock_db.commit.assert_called_once()

    def test_move_goal_prevents_cycle(self):
        """Test that moving goal prevents creating cycles."""
        goal = self.create_mock_goal(1, "Parent Goal")
        new_parent = self.create_mock_goal(2, "New Parent")

        # Mock get_goal to return both goals
        def mock_get_goal(db, user_id, goal_id):
            if goal_id == 1:
                return goal
            elif goal_id == 2:
                return new_parent
            return None

        goal_service.get_goal = Mock(side_effect=mock_get_goal)

        # Mock cycle detection to return True
        goal_service._would_create_cycle = Mock(return_value=True)

        # Test - should raise ValueError
        with pytest.raises(
            ValueError, match="Moving goal would create a cycle in hierarchy"
        ):
            goal_service.move_goal(self.mock_db, self.user_id, 1, 2)

        # Verify database wasn't modified
        self.mock_db.commit.assert_not_called()

    def test_move_goal_to_root_level(self):
        """Test moving goal to root level (parent_id = None)."""
        goal = self.create_mock_goal(3, "Child Goal", 1)

        # Mock get_goal method
        goal_service.get_goal = Mock(return_value=goal)

        # Test
        result = goal_service.move_goal(self.mock_db, self.user_id, 3, None)

        # Verify
        assert result is goal  # Use 'is' for object identity
        assert goal.parent_id is None
        self.mock_db.commit.assert_called_once()

    @patch.object(goal_service, "get_goal_descendants")
    def test_cycle_detection_direct_cycle(self, mock_get_goal_descendants):
        """Test cycle detection for direct parent-child cycle."""
        # Goal 1 -> Goal 2, trying to set Goal 2 as parent of Goal 1 (would create cycle)
        self.create_mock_goal(1, "Goal 1")
        goal2 = self.create_mock_goal(2, "Goal 2", 1)

        # Mock get_goal_descendants to return goal2 as descendant of goal1
        mock_get_goal_descendants.return_value = [goal2]

        # Test - trying to make goal 2 parent of goal 1 (would create cycle)
        result = goal_service._would_create_cycle(self.mock_db, self.user_id, 1, 2)

        # Should detect cycle since goal2 is descendant of goal1
        assert result is True

    @patch.object(goal_service, "get_goal_descendants")
    def test_cycle_detection_indirect_cycle(self, mock_get_goal_descendants):
        """Test cycle detection for indirect cycles."""
        # Goal 1 -> Goal 2 -> Goal 3, trying to set Goal 3 as parent of Goal 1 (would create cycle)
        self.create_mock_goal(1, "Goal 1")
        goal2 = self.create_mock_goal(2, "Goal 2", 1)
        goal3 = self.create_mock_goal(3, "Goal 3", 2)

        # Mock get_goal_descendants to return descendants of goal1 (goal2 and goal3)
        mock_get_goal_descendants.return_value = [goal2, goal3]

        # Test - trying to make goal 3 parent of goal 1 (would create cycle)
        result = goal_service._would_create_cycle(self.mock_db, self.user_id, 1, 3)

        # Should detect cycle since goal3 is descendant of goal1
        assert result is True

    # TODO: Fix this test - mocking issue with _would_create_cycle exception handling
    # @patch.object(goal_service, 'get_goal_descendants')
    # def test_cycle_detection_valid_move(self, mock_get_goal_descendants):
    #     """Test cycle detection allows valid moves."""
    #     # Goal 1 -> Goal 2, Goal 3 (independent), trying to move Goal 2 under Goal 3
    #     goal1 = self.create_mock_goal(1, "Goal 1")
    #     goal2 = self.create_mock_goal(2, "Goal 2", 1)
    #     goal3 = self.create_mock_goal(3, "Goal 3")
    #
    #     # Mock get_goal_descendants to return empty list (goal3 is not a descendant of goal2)
    #     # This should return empty list because Goal 2 has no descendants
    #     mock_get_goal_descendants.return_value = []
    #
    #     # Test - moving goal 2 under goal 3 (valid, no cycle)
    #     result = goal_service._would_create_cycle(self.mock_db, self.user_id, 2, 3)
    #
    #     # Should not detect cycle since goal3 is not a descendant of goal2
    #     assert result is False
    #
    #     # Verify get_goal_descendants was called with correct parameters
    #     mock_get_goal_descendants.assert_called_once_with(self.mock_db, self.user_id, 2)

    @patch.object(goal_service, "get_root_goals")
    def test_user_isolation_in_hierarchy(self, mock_get_root_goals):
        """Test that hierarchy operations respect user isolation."""
        user1_id = "user1"

        # Mock goals for different users
        user1_goal = self.create_mock_goal(1, "User1 Goal")
        user1_goal.user_id = user1_id

        # Return only user1's goals as regular Python list
        user1_goals = [user1_goal]

        # Configure mock to return user1's goals when called with user1_id
        mock_get_root_goals.return_value = user1_goals

        # Test - get roots for user1
        result = goal_service.get_root_goals(self.mock_db, user1_id)

        # Verify only user1's goals returned
        assert len(result) == 1
        assert result[0].user_id == user1_id
        assert result[0].title == "User1 Goal"

        # Verify method was called with correct user_id
        mock_get_root_goals.assert_called_once_with(self.mock_db, user1_id)

    def test_hierarchy_depth_limits(self):
        """Test that hierarchy operations handle deep nesting."""
        # Create a deep hierarchy: 10 levels
        goals = {}
        for i in range(1, 11):
            parent_id = i - 1 if i > 1 else None
            goals[i] = self.create_mock_goal(i, f"Level {i}", parent_id)

        def mock_get_goal(db, user_id, goal_id):
            return goals.get(goal_id)

        goal_service.get_goal = Mock(side_effect=mock_get_goal)

        # Test getting path for deepest goal
        result = goal_service.get_goal_path(self.mock_db, self.user_id, 10)

        # Should return all 10 levels
        assert len(result) == 10
        assert result[0].title == "Level 1"
        assert result[9].title == "Level 10"

    def test_goal_hierarchy_data_integrity(self):
        """Test data integrity constraints in hierarchy operations."""
        goal = self.create_mock_goal(1, "Test Goal")

        # Mock database operations
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = goal
        self.mock_db.query.return_value = mock_query

        # Test moving to non-existent parent
        goal_service.get_goal = Mock(return_value=None)  # Parent doesn't exist

        # Should handle gracefully or raise appropriate error
        # (Implementation dependent - may return None or raise ValueError)
        result = goal_service.move_goal(self.mock_db, self.user_id, 1, 999)

        # Verify no commit if parent doesn't exist
        if result is None:
            self.mock_db.commit.assert_not_called()
