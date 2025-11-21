"""Task repository interface.

Abstract base class for task repositories.
Following Repository Pattern for clean separation of concerns.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.task import Task


class TaskRepositoryInterface(ABC):
    """Abstract interface for task repositories.
    
    This interface defines the contract for task data access.
    Implementations can be for Jira, Notion, Database, etc.
    """

    @abstractmethod
    def create(self, task: Task) -> Task:
        """Create a new task.
        
        Args:
            task: Task to create
            
        Returns:
            Created task with updated IDs
        """
        pass

    @abstractmethod
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task if found, None otherwise
        """
        pass

    @abstractmethod
    def update(self, task: Task) -> Task:
        """Update existing task.
        
        Args:
            task: Task with updated data
            
        Returns:
            Updated task
        """
        pass

    @abstractmethod
    def list_by_department(self, department_id: str) -> List[Task]:
        """List all tasks for a department.
        
        Args:
            department_id: Department identifier
            
        Returns:
            List of tasks
        """
        pass

    @abstractmethod
    def list_by_sprint(self, sprint_id: str) -> List[Task]:
        """List all tasks in a sprint.
        
        Args:
            sprint_id: Sprint identifier
            
        Returns:
            List of tasks
        """
        pass

    @abstractmethod
    def list_by_assignee(self, assignee_id: str) -> List[Task]:
        """List all tasks assigned to a user.
        
        Args:
            assignee_id: User identifier
            
        Returns:
            List of tasks
        """
        pass


