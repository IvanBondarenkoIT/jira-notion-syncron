"""Unit tests for domain models."""

from datetime import date, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.domain.models import Department, Sprint, Task, User
from src.domain.models.sprint import SprintStatus
from src.domain.models.task import Priority, TaskStatus, TaskType
from src.domain.models.user import UserRole


class TestUser:
    """Tests for User model."""

    def test_user_creation(self) -> None:
        """Test user creation with valid data."""
        user = User(
            id="user_001",
            name="Test",
            full_name="Test User",
            email="test@example.com",
            department="marketing",
            role=UserRole.MARKETING_SPECIALIST,
        )
        
        assert user.id == "user_001"
        assert user.name == "Test"
        assert user.is_active()

    def test_user_display_name(self) -> None:
        """Test user display name."""
        user = User(
            id="user_001",
            name="Test",
            full_name="Test User",
            email="test@example.com",
            department="marketing",
            role=UserRole.MARKETING_SPECIALIST,
        )
        
        assert user.get_display_name() == "Test"

    def test_user_invalid_email(self) -> None:
        """Test user creation with invalid email."""
        with pytest.raises(ValidationError):
            User(
                id="user_001",
                name="Test",
                full_name="Test User",
                email="invalid-email",
                department="marketing",
                role=UserRole.MARKETING_SPECIALIST,
            )


class TestTask:
    """Tests for Task model."""

    def test_task_creation(self) -> None:
        """Test task creation with valid data."""
        task = Task(
            title="Test Task",
            department_id="marketing",
            task_type=TaskType.TASK,
            priority=Priority.HIGH,
        )
        
        assert task.title == "Test Task"
        assert task.priority == Priority.HIGH
        assert task.status == TaskStatus.TODO

    def test_task_completed(self) -> None:
        """Test task completion check."""
        task = Task(
            title="Test Task",
            department_id="marketing",
            status=TaskStatus.DONE,
        )
        
        assert task.is_completed()

    def test_task_has_assignee(self) -> None:
        """Test task assignee check."""
        task = Task(
            title="Test Task",
            department_id="marketing",
            assignee_id="user_001",
        )
        
        assert task.has_assignee()


class TestSprint:
    """Tests for Sprint model."""

    def test_sprint_creation(self) -> None:
        """Test sprint creation with valid data."""
        start = date.today()
        end = start + timedelta(days=6)
        
        sprint = Sprint(
            name="Test Sprint",
            department_id="marketing",
            start_date=start,
            end_date=end,
        )
        
        assert sprint.name == "Test Sprint"
        assert sprint.get_duration_days() == 7

    def test_sprint_invalid_dates(self) -> None:
        """Test sprint creation with invalid dates."""
        start = date.today()
        end = start - timedelta(days=1)  # End before start
        
        with pytest.raises(ValidationError):
            Sprint(
                name="Test Sprint",
                department_id="marketing",
                start_date=start,
                end_date=end,
            )

    def test_sprint_completion_percentage(self) -> None:
        """Test sprint completion percentage calculation."""
        sprint = Sprint(
            name="Test Sprint",
            department_id="marketing",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
            total_story_points=40,
            completed_story_points=20,
        )
        
        assert sprint.get_completion_percentage() == 50.0

    def test_sprint_add_task(self) -> None:
        """Test adding task to sprint."""
        sprint = Sprint(
            name="Test Sprint",
            department_id="marketing",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
        )
        
        sprint.add_task("task_001")
        assert "task_001" in sprint.task_ids
        assert len(sprint.task_ids) == 1


class TestDepartment:
    """Tests for Department model."""

    def test_department_creation(self) -> None:
        """Test department creation with valid data."""
        dept = Department(
            id="marketing",
            name="Маркетинг",
            name_en="Marketing",
            members=["user_001", "user_002"],
        )
        
        assert dept.id == "marketing"
        assert dept.get_member_count() == 2

    def test_department_has_jira_board(self) -> None:
        """Test department Jira board check."""
        dept = Department(
            id="marketing",
            name="Маркетинг",
            name_en="Marketing",
            jira_board_id="123",
        )
        
        assert dept.has_jira_board()

