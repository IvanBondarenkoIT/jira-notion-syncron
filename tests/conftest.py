"""Pytest configuration and fixtures."""

from datetime import date, datetime
from typing import Generator

import pytest

from src.domain.models import Department, Sprint, Task, User
from src.domain.models.task import Priority, TaskStatus, TaskType
from src.domain.models.sprint import SprintStatus
from src.domain.models.user import UserRole


@pytest.fixture
def sample_user() -> User:
    """Create a sample user for testing."""
    return User(
        id="user_test_001",
        name="Test User",
        full_name="Test User Full Name",
        email="test@example.com",
        department="marketing",
        role=UserRole.MARKETING_SPECIALIST,
        active=True,
    )


@pytest.fixture
def sample_department() -> Department:
    """Create a sample department for testing."""
    return Department(
        id="dept_test_001",
        name="Test Department",
        name_en="Test Department",
        description="Test department description",
        members=["user_001", "user_002"],
        workflow=["Backlog", "To Do", "In Progress", "Done"],
        task_types=["Task", "Bug", "Story"],
        sprint_duration_days=7,
    )


@pytest.fixture
def sample_task() -> Task:
    """Create a sample task for testing."""
    return Task(
        id="task_test_001",
        title="Test Task",
        description="Test task description",
        task_type=TaskType.TASK,
        priority=Priority.MEDIUM,
        status=TaskStatus.TODO,
        department_id="dept_test_001",
        assignee_id="user_test_001",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_sprint() -> Sprint:
    """Create a sample sprint for testing."""
    start = date.today()
    end = date(start.year, start.month, start.day + 6)
    
    return Sprint(
        id="sprint_test_001",
        name="Test Sprint",
        goal="Test sprint goal",
        department_id="dept_test_001",
        start_date=start,
        end_date=end,
        status=SprintStatus.ACTIVE,
        total_story_points=40,
        completed_story_points=0,
    )


@pytest.fixture
def temp_data_dir(tmp_path) -> Generator:
    """Create a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (data_dir / "archive").mkdir()
    
    yield data_dir
    
    # Cleanup is automatic with tmp_path

