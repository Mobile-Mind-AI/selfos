"""
Unit tests for HabitService

Tests the business logic layer for habit management.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from services.habit_service import HabitService
import schemas
import models


class TestHabitService:
    """Test suite for HabitService"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.habit_service = HabitService()
        self.mock_db = Mock()
        self.user_id = "test_user_123"
        
        # Sample habit data
        self.sample_recurrence_rule = schemas.RecurrenceRule(
            type="weekly",
            target_count=3,
            target_type="count"
        )
        
        self.sample_habit_create = schemas.HabitCreate(
            title="Exercise",
            description="Go to the gym",
            recurrence_rule=self.sample_recurrence_rule,
            is_active=True,
            goal_id=1,
            life_area_id=1
        )
        
        # Mock habit model
        self.mock_habit = Mock(spec=models.Habit)
        self.mock_habit.id = 1
        self.mock_habit.user_id = self.user_id
        self.mock_habit.title = "Exercise"
        self.mock_habit.description = "Go to the gym"
        self.mock_habit.recurrence_rule = {"type": "weekly", "target_count": 3, "target_type": "count"}
        self.mock_habit.is_active = True
        self.mock_habit.current_streak = 5
        self.mock_habit.best_streak = 10
        self.mock_habit.total_completions = 25
        self.mock_habit.goal = None
        self.mock_habit.life_area = None

    def test_get_habit_success(self):
        """Test successful habit retrieval"""
        # Setup
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = self.mock_habit
        
        # Execute
        result = self.habit_service.get_habit(self.mock_db, self.user_id, 1)
        
        # Verify
        assert result == self.mock_habit
        self.mock_db.query.assert_called_once_with(models.Habit)

    def test_get_habit_not_found(self):
        """Test habit retrieval when habit doesn't exist"""
        # Setup
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = self.habit_service.get_habit(self.mock_db, self.user_id, 999)
        
        # Verify
        assert result is None

    def test_create_habit_success(self):
        """Test successful habit creation"""
        # Setup
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        # Mock the created habit
        created_habit = Mock(spec=models.Habit)
        created_habit.id = 1
        created_habit.title = "Exercise"
        
        # Execute
        with patch('models.Habit', return_value=created_habit):
            result = self.habit_service.create_habit(self.mock_db, self.user_id, self.sample_habit_create)
        
        # Verify
        assert result == created_habit
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_list_habits_all(self):
        """Test listing all habits for a user"""
        # Setup
        mock_habits = [self.mock_habit]
        self.mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = mock_habits
        
        # Execute
        result = self.habit_service.list_habits(self.mock_db, self.user_id)
        
        # Verify
        assert result == mock_habits
        assert len(result) == 1

    def test_list_habits_active_only(self):
        """Test listing only active habits"""
        # Setup
        mock_habits = [self.mock_habit]
        query_mock = self.mock_db.query.return_value.options.return_value.filter.return_value
        query_mock.filter.return_value.all.return_value = mock_habits
        
        # Execute
        result = self.habit_service.list_habits(self.mock_db, self.user_id, is_active=True)
        
        # Verify
        assert result == mock_habits
        # Verify filter was called twice (once for user_id, once for is_active)
        assert query_mock.filter.call_count == 1

    def test_update_habit_success(self):
        """Test successful habit update"""
        # Setup
        update_data = schemas.HabitUpdate(title="Updated Exercise")
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = self.mock_habit
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        # Execute
        result = self.habit_service.update_habit(self.mock_db, self.user_id, 1, update_data)
        
        # Verify
        assert result == self.mock_habit
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_update_habit_not_found(self):
        """Test habit update when habit doesn't exist"""
        # Setup
        update_data = schemas.HabitUpdate(title="Updated Exercise")
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = self.habit_service.update_habit(self.mock_db, self.user_id, 999, update_data)
        
        # Verify
        assert result is None

    def test_delete_habit_success(self):
        """Test successful habit deletion"""
        # Setup
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_habit
        self.mock_db.delete = Mock()
        self.mock_db.commit = Mock()
        
        # Execute
        result = self.habit_service.delete_habit(self.mock_db, self.user_id, 1)
        
        # Verify
        assert result is True
        self.mock_db.delete.assert_called_once_with(self.mock_habit)
        self.mock_db.commit.assert_called_once()

    def test_delete_habit_not_found(self):
        """Test habit deletion when habit doesn't exist"""
        # Setup
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = self.habit_service.delete_habit(self.mock_db, self.user_id, 999)
        
        # Verify
        assert result is False

    def test_complete_habit_success(self):
        """Test successful habit completion"""
        # Setup
        completion_data = schemas.HabitCompletionCreate(
            notes="Good workout today"
        )
        
        # Reset previous side_effect and return_value settings
        self.mock_db.reset_mock()
        
        # Configure mocks for the habit query chain
        habit_filter_mock = Mock()
        habit_filter_mock.first.return_value = self.mock_habit
        habit_query_mock = Mock()
        habit_query_mock.filter.return_value = habit_filter_mock
        
        # Configure mocks for the completion check query chain  
        completion_filter_mock = Mock()
        completion_filter_mock.first.return_value = None  # No existing completion
        completion_query_mock = Mock()
        completion_query_mock.filter.return_value = completion_filter_mock
        
        # Set up side_effect for different database queries
        self.mock_db.query.side_effect = [
            habit_query_mock,  # First query for habit lookup
            completion_query_mock  # Second query for existing completion check
        ]
        
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        # Mock the created completion
        mock_completion = Mock(spec=models.HabitCompletion)
        mock_completion.id = 1
        mock_completion.habit_id = 1
        
        # Execute
        with patch('models.HabitCompletion', return_value=mock_completion):
            with patch.object(self.habit_service, '_update_habit_stats'):
                result = self.habit_service.complete_habit(self.mock_db, self.user_id, 1, completion_data)
        
        # Verify
        assert result == mock_completion
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_complete_habit_already_completed_today(self):
        """Test completing habit when already completed today"""
        # Setup
        completion_data = schemas.HabitCompletionCreate()
        
        existing_completion = Mock(spec=models.HabitCompletion)
        existing_completion.id = 1
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            self.mock_habit,  # First query for habit
            existing_completion  # Second query for existing completion
        ]
        
        # Execute
        result = self.habit_service.complete_habit(self.mock_db, self.user_id, 1, completion_data)
        
        # Verify - should return existing completion
        assert result == existing_completion

    def test_complete_habit_not_found(self):
        """Test completing habit when habit doesn't exist or is inactive"""
        # Setup
        completion_data = schemas.HabitCompletionCreate()
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = self.habit_service.complete_habit(self.mock_db, self.user_id, 999, completion_data)
        
        # Verify
        assert result is None

    def test_get_current_period_daily(self):
        """Test period calculation for daily habits"""
        # Setup
        recurrence_rule = {"type": "daily", "target_count": 1}
        target_date = date(2024, 1, 15)
        
        # Execute
        start_date, end_date = self.habit_service._get_current_period(recurrence_rule, target_date)
        
        # Verify
        assert start_date == target_date
        assert end_date == target_date

    def test_get_current_period_weekly(self):
        """Test period calculation for weekly habits"""
        # Setup
        recurrence_rule = {"type": "weekly", "target_count": 3}
        target_date = date(2024, 1, 17)  # Wednesday
        
        # Execute
        start_date, end_date = self.habit_service._get_current_period(recurrence_rule, target_date)
        
        # Verify - should return Monday to Sunday of that week
        assert start_date == date(2024, 1, 15)  # Monday
        assert end_date == date(2024, 1, 21)    # Sunday

    def test_get_current_period_monthly(self):
        """Test period calculation for monthly habits"""
        # Setup
        recurrence_rule = {"type": "monthly", "target_count": 10}
        target_date = date(2024, 1, 15)
        
        # Execute
        start_date, end_date = self.habit_service._get_current_period(recurrence_rule, target_date)
        
        # Verify - should return first and last day of month
        assert start_date == date(2024, 1, 1)   # First of January
        assert end_date == date(2024, 1, 31)    # Last of January

    def test_calculate_current_streak(self):
        """Test streak calculation"""
        # Setup
        habit_id = 1
        completion_date = date(2024, 1, 15)
        
        # Mock completions - consecutive days
        mock_completions = [
            Mock(completion_date=date(2024, 1, 15)),  # Today
            Mock(completion_date=date(2024, 1, 14)),  # Yesterday
            Mock(completion_date=date(2024, 1, 13)),  # Day before
            Mock(completion_date=date(2024, 1, 11)),  # Gap here - should stop at 3
        ]
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_completions
        
        # Execute
        streak = self.habit_service._calculate_current_streak(self.mock_db, habit_id, completion_date)
        
        # Verify - should be 3 (stops at the gap)
        assert streak == 3

    def test_calculate_current_streak_no_completions(self):
        """Test streak calculation with no completions"""
        # Setup
        habit_id = 1
        completion_date = date(2024, 1, 15)
        
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Execute
        streak = self.habit_service._calculate_current_streak(self.mock_db, habit_id, completion_date)
        
        # Verify
        assert streak == 0

    def test_update_habit_stats(self):
        """Test habit statistics update"""
        # Setup
        completion_date = date.today()
        self.mock_habit.total_completions = 10
        self.mock_habit.current_streak = 5
        self.mock_habit.best_streak = 8
        
        # Execute
        with patch.object(self.habit_service, '_calculate_current_streak', return_value=6):
            self.habit_service._update_habit_stats(self.mock_db, self.mock_habit, completion_date)
        
        # Verify
        assert self.mock_habit.total_completions == 11
        assert self.mock_habit.current_streak == 6
        assert self.mock_habit.best_streak == 8  # Shouldn't change since 6 < 8

    def test_update_habit_stats_new_best_streak(self):
        """Test habit statistics update with new best streak"""
        # Setup
        completion_date = date.today()
        self.mock_habit.total_completions = 10
        self.mock_habit.current_streak = 5
        self.mock_habit.best_streak = 8
        
        # Execute
        with patch.object(self.habit_service, '_calculate_current_streak', return_value=10):
            self.habit_service._update_habit_stats(self.mock_db, self.mock_habit, completion_date)
        
        # Verify
        assert self.mock_habit.total_completions == 11
        assert self.mock_habit.current_streak == 10
        assert self.mock_habit.best_streak == 10  # Should update to new best

    @pytest.mark.parametrize("recurrence_type,expected_days", [
        ("daily", 1),
        ("weekly", 7),
        ("monthly", 31),  # January has 31 days
    ])
    def test_period_calculation_parametrized(self, recurrence_type, expected_days):
        """Test period calculation for different recurrence types"""
        # Setup
        recurrence_rule = {"type": recurrence_type, "target_count": 1}
        target_date = date(2024, 1, 15)  # January 15, 2024
        
        # Execute
        start_date, end_date = self.habit_service._get_current_period(recurrence_rule, target_date)
        
        # Verify
        days_in_period = (end_date - start_date).days + 1
        assert days_in_period == expected_days
