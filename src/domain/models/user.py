"""User domain model."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles in the system."""

    DIRECTOR = "director"
    MARKETING_SPECIALIST = "marketing_specialist"
    HR_SPECIALIST = "hr_specialist"
    DEVELOPER = "developer"
    MANAGER = "manager"


class User(BaseModel):
    """User domain model."""

    id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., min_length=1, max_length=100, description="User display name")
    full_name: str = Field(..., min_length=1, max_length=200, description="Full user name")
    email: EmailStr = Field(..., description="User email address")
    department: str = Field(..., description="Department ID")
    role: UserRole = Field(..., description="User role")
    
    # External system IDs
    jira_account_id: Optional[str] = Field(None, description="Jira account ID")
    notion_user_id: Optional[str] = Field(None, description="Notion user ID")
    
    # Status
    active: bool = Field(True, description="Whether user is active")
    hire_date: Optional[date] = Field(None, description="Date when user was hired")
    
    # Additional info
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "user_001",
                "name": "Саша",
                "full_name": "Александр Петров",
                "email": "sasha@company.com",
                "department": "marketing",
                "role": "marketing_specialist",
                "jira_account_id": "5b10a2844c20165700ede21g",
                "notion_user_id": "92a8d021-2e4c-4d5f-8c3a-9b3c2e1f4d5a",
                "active": True,
                "hire_date": "2024-01-15",
                "notes": "",
            }
        }

    def get_display_name(self) -> str:
        """Get user display name."""
        return self.name or self.full_name

    def is_active(self) -> bool:
        """Check if user is active."""
        return self.active

    def has_jira_account(self) -> bool:
        """Check if user has Jira account."""
        return bool(self.jira_account_id)

    def has_notion_account(self) -> bool:
        """Check if user has Notion account."""
        return bool(self.notion_user_id)

