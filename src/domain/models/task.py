"""Task domain model."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""

    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Task priority enumeration."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(str, Enum):
    """Task type enumeration."""

    STORY = "story"
    TASK = "task"
    BUG = "bug"
    EPIC = "epic"
    SUBTASK = "subtask"


class Task(BaseModel):
    """Task domain model."""

    id: Optional[str] = Field(None, description="Unique task identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    
    # Classification
    task_type: TaskType = Field(TaskType.TASK, description="Task type")
    priority: Priority = Field(Priority.MEDIUM, description="Task priority")
    status: TaskStatus = Field(TaskStatus.TODO, description="Task status")
    
    # Assignment
    assignee_id: Optional[str] = Field(None, description="Assigned user ID")
    department_id: str = Field(..., description="Department ID")
    
    # External system IDs
    jira_issue_key: Optional[str] = Field(None, description="Jira issue key (e.g., PROJ-123)")
    notion_page_id: Optional[str] = Field(None, description="Notion page ID")
    
    # Sprint
    sprint_id: Optional[str] = Field(None, description="Sprint ID")
    story_points: Optional[int] = Field(None, ge=0, le=100, description="Story points")
    
    # Dates
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Update timestamp")
    due_date: Optional[datetime] = Field(None, description="Due date")
    
    # Additional
    labels: List[str] = Field(default_factory=list, description="Task labels")
    comments_count: int = Field(0, ge=0, description="Number of comments")
    
    # Source tracking
    source: str = Field("manual", description="Source of task (jira, notion, csv, telegram, manual)")
    source_data: Optional[dict] = Field(None, description="Original source data")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "task_001",
                "title": "Создать контент-план на неделю",
                "description": "Подготовить контент-план для соцсетей на следующую неделю",
                "task_type": "task",
                "priority": "high",
                "status": "in_progress",
                "assignee_id": "user_001",
                "department_id": "marketing",
                "jira_issue_key": "MARK-123",
                "notion_page_id": "abc123",
                "sprint_id": "sprint_001",
                "story_points": 5,
                "labels": ["контент", "smm"],
                "source": "notion",
            }
        }

    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.DONE

    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date:
            return False
        return datetime.now() > self.due_date and not self.is_completed()

    def has_assignee(self) -> bool:
        """Check if task has assignee."""
        return bool(self.assignee_id)

    def in_jira(self) -> bool:
        """Check if task exists in Jira."""
        return bool(self.jira_issue_key)

    def in_notion(self) -> bool:
        """Check if task exists in Notion."""
        return bool(self.notion_page_id)

