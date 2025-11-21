"""Use case: Create task in Jira.

Business logic for creating tasks in Jira.
"""

import logging
from typing import Optional

from src.domain.models.task import Task
from src.domain.repositories.task_repository import TaskRepositoryInterface

logger = logging.getLogger(__name__)


class CreateTaskInJiraUseCase:
    """Use case for creating tasks in Jira.
    
    Encapsulates the business logic for task creation,
    including validation and error handling.
    """

    def __init__(self, task_repository: TaskRepositoryInterface) -> None:
        """Initialize use case.
        
        Args:
            task_repository: Repository for task persistence
        """
        self.task_repository = task_repository

    def execute(
        self,
        title: str,
        department_id: str,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        **kwargs
    ) -> Task:
        """Create a new task in Jira.
        
        Args:
            title: Task title (required)
            department_id: Department ID (required)
            description: Task description (optional)
            assignee_id: Assignee Jira account ID (optional)
            **kwargs: Additional task parameters
            
        Returns:
            Created task with Jira issue key
            
        Raises:
            ValueError: If validation fails
            
        Example:
            >>> use_case = CreateTaskInJiraUseCase(jira_repository)
            >>> task = use_case.execute(
            ...     title="Create content plan",
            ...     department_id="marketing",
            ...     description="Weekly content plan",
            ...     assignee_id="712020:abc123...",
            ...     priority=Priority.HIGH,
            ...     labels=["content", "smm"]
            ... )
        """
        # Validation
        if not title or len(title.strip()) == 0:
            raise ValueError("Task title is required")
        
        if not department_id:
            raise ValueError("Department ID is required")

        logger.info(f"Creating task: {title} for department: {department_id}")

        # Create task domain model
        task = Task(
            title=title.strip(),
            department_id=department_id,
            description=description,
            assignee_id=assignee_id,
            **kwargs
        )

        # Validate task (Pydantic will raise if invalid)
        task.model_validate(task.model_dump())

        # Create in repository (Jira)
        created_task = self.task_repository.create(task)

        logger.info(f"Task created successfully: {created_task.jira_issue_key}")
        
        return created_task



