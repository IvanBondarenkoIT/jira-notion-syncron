"""Sprint domain model."""

from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SprintStatus(str, Enum):
    """Sprint status enumeration."""

    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Sprint(BaseModel):
    """Sprint domain model."""

    id: Optional[str] = Field(None, description="Unique sprint identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Sprint name")
    goal: Optional[str] = Field(None, description="Sprint goal")
    
    # Department
    department_id: str = Field(..., description="Department ID")
    
    # Dates
    start_date: date = Field(..., description="Sprint start date")
    end_date: date = Field(..., description="Sprint end date")
    
    # Status
    status: SprintStatus = Field(SprintStatus.PLANNED, description="Sprint status")
    
    # External system IDs
    jira_sprint_id: Optional[str] = Field(None, description="Jira sprint ID")
    
    # Tasks
    task_ids: List[str] = Field(default_factory=list, description="List of task IDs in sprint")
    
    # Metrics
    total_story_points: int = Field(0, ge=0, description="Total story points")
    completed_story_points: int = Field(0, ge=0, description="Completed story points")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Update timestamp")

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: date, info) -> date:
        """Validate that end_date is after start_date."""
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "sprint_001",
                "name": "Спринт 43 (21-27 октября)",
                "goal": "Запустить новую рекламную кампанию",
                "department_id": "marketing",
                "start_date": "2024-10-21",
                "end_date": "2024-10-27",
                "status": "active",
                "jira_sprint_id": "123",
                "task_ids": ["task_001", "task_002"],
                "total_story_points": 40,
                "completed_story_points": 15,
            }
        }

    def is_active(self) -> bool:
        """Check if sprint is currently active."""
        return self.status == SprintStatus.ACTIVE

    def is_completed(self) -> bool:
        """Check if sprint is completed."""
        return self.status == SprintStatus.COMPLETED

    def get_duration_days(self) -> int:
        """Get sprint duration in days."""
        return (self.end_date - self.start_date).days + 1

    def get_completion_percentage(self) -> float:
        """Get sprint completion percentage."""
        if self.total_story_points == 0:
            return 0.0
        return (self.completed_story_points / self.total_story_points) * 100

    def days_remaining(self) -> int:
        """Get number of days remaining in sprint."""
        if self.is_completed():
            return 0
        today = date.today()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days

    def add_task(self, task_id: str) -> None:
        """Add task to sprint."""
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
            self.updated_at = datetime.now()

    def remove_task(self, task_id: str) -> None:
        """Remove task from sprint."""
        if task_id in self.task_ids:
            self.task_ids.remove(task_id)
            self.updated_at = datetime.now()

