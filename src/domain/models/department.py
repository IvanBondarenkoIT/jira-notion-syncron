"""Department domain model."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DepartmentRole(str, Enum):
    """Department types."""

    MARKETING = "marketing"
    HR = "hr"
    DEVELOPMENT = "development"
    MANAGEMENT = "management"
    SALES = "sales"
    SUPPORT = "support"


class WorkflowStage(BaseModel):
    """Workflow stage model."""

    name: str = Field(..., description="Stage name")
    order: int = Field(..., description="Stage order")


class Department(BaseModel):
    """Department domain model."""

    id: str = Field(..., description="Unique department identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Department name")
    name_en: str = Field(..., description="Department name in English")
    description: Optional[str] = Field(None, description="Department description")
    
    # External system IDs
    jira_board_id: Optional[str] = Field(None, description="Jira board ID")
    notion_database_id: Optional[str] = Field(None, description="Notion database ID")
    
    # Members
    members: List[str] = Field(default_factory=list, description="List of user IDs")
    
    # Workflow
    workflow: List[str] = Field(
        default_factory=lambda: ["Backlog", "To Do", "In Progress", "Review", "Done"],
        description="Workflow stages",
    )
    
    # Task types
    task_types: List[str] = Field(default_factory=list, description="Available task types")
    
    # Sprint settings
    sprint_duration_days: int = Field(7, description="Sprint duration in days")
    sprint_start_day: str = Field("monday", description="Sprint start day")
    
    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "marketing",
                "name": "Маркетинг",
                "name_en": "Marketing",
                "description": "Отдел маркетинга и продвижения",
                "jira_board_id": "123",
                "notion_database_id": "abc123",
                "members": ["user_001", "user_002"],
                "workflow": ["Backlog", "To Do", "In Progress", "Review", "Done"],
                "task_types": ["Контент", "SMM", "Реклама"],
                "sprint_duration_days": 7,
                "sprint_start_day": "monday",
            }
        }

    def has_jira_board(self) -> bool:
        """Check if department has Jira board."""
        return bool(self.jira_board_id)

    def has_notion_database(self) -> bool:
        """Check if department has Notion database."""
        return bool(self.notion_database_id)

    def get_member_count(self) -> int:
        """Get number of members in department."""
        return len(self.members)

