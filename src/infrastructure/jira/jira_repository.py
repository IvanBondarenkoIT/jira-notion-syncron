"""Jira repository implementation.

Implements TaskRepositoryInterface for Jira.
Maps between Domain models and Jira API format.
"""

import logging
from datetime import datetime
from typing import List, Optional

from src.domain.models.task import Priority, Task, TaskStatus, TaskType
from src.domain.repositories.task_repository import TaskRepositoryInterface
from src.infrastructure.jira.jira_client import JiraClient

logger = logging.getLogger(__name__)


class JiraTaskRepository(TaskRepositoryInterface):
    """Jira implementation of TaskRepository.
    
    Handles mapping between Task domain model and Jira API format.
    """

    # Mapping between our domain model and Jira
    STATUS_MAPPING = {
        TaskStatus.BACKLOG: "Backlog",
        TaskStatus.TODO: "To Do",
        TaskStatus.IN_PROGRESS: "In Progress",
        TaskStatus.REVIEW: "Review",
        TaskStatus.DONE: "Done",
        TaskStatus.CANCELLED: "Cancelled",
    }

    REVERSE_STATUS_MAPPING = {v: k for k, v in STATUS_MAPPING.items()}

    PRIORITY_MAPPING = {
        Priority.CRITICAL: "Highest",
        Priority.HIGH: "High",
        Priority.MEDIUM: "Medium",
        Priority.LOW: "Low",
    }

    REVERSE_PRIORITY_MAPPING = {v: k for k, v in PRIORITY_MAPPING.items()}

    TYPE_MAPPING = {
        TaskType.STORY: "Story",
        TaskType.TASK: "Task",
        TaskType.BUG: "Bug",
        TaskType.EPIC: "Epic",
        TaskType.SUBTASK: "Sub-task",
    }

    REVERSE_TYPE_MAPPING = {v: k for k, v in TYPE_MAPPING.items()}

    def __init__(self, client: JiraClient, project_key: str) -> None:
        """Initialize Jira repository.
        
        Args:
            client: Configured Jira client
            project_key: Jira project key (e.g., PROJ)
        """
        self.client = client
        self.project_key = project_key
        logger.info(f"Initialized Jira repository for project: {project_key}")

    def _task_to_jira_format(self, task: Task) -> dict:
        """Convert Task domain model to Jira API format.
        
        Args:
            task: Domain task model
            
        Returns:
            Jira API format dictionary
        """
        fields = {
            "project": {"key": self.project_key},
            "summary": task.title,
            "issuetype": {"name": self.TYPE_MAPPING.get(task.task_type, "Task")},
        }

        # Description (Atlassian Document Format)
        if task.description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": task.description
                            }
                        ]
                    }
                ]
            }

        # Priority
        if task.priority:
            fields["priority"] = {"name": self.PRIORITY_MAPPING.get(task.priority, "Medium")}

        # Assignee
        if task.assignee_id:
            fields["assignee"] = {"accountId": task.assignee_id}

        # Story points (if available as custom field)
        if task.story_points:
            # Note: Story points field ID varies by Jira instance
            # Typically customfield_10016 or similar
            # fields["customfield_10016"] = task.story_points
            pass

        # Labels
        if task.labels:
            fields["labels"] = task.labels

        # Due date
        if task.due_date:
            fields["duedate"] = task.due_date.strftime("%Y-%m-%d")

        return {"fields": fields}

    def _jira_to_task(self, jira_issue: dict, department_id: str) -> Task:
        """Convert Jira issue to Task domain model.
        
        Args:
            jira_issue: Jira API issue dictionary
            department_id: Department ID for the task
            
        Returns:
            Task domain model
        """
        fields = jira_issue.get("fields", {})

        # Extract description text
        description = ""
        desc_obj = fields.get("description")
        if desc_obj and isinstance(desc_obj, dict):
            # Parse Atlassian Document Format
            content = desc_obj.get("content", [])
            texts = []
            for block in content:
                if block.get("type") == "paragraph":
                    para_content = block.get("content", [])
                    for item in para_content:
                        if item.get("type") == "text":
                            texts.append(item.get("text", ""))
            description = "\n".join(texts)

        # Status
        status_name = fields.get("status", {}).get("name", "To Do")
        status = self.REVERSE_STATUS_MAPPING.get(status_name, TaskStatus.TODO)

        # Priority
        priority_name = fields.get("priority", {}).get("name", "Medium")
        priority = self.REVERSE_PRIORITY_MAPPING.get(priority_name, Priority.MEDIUM)

        # Task type
        type_name = fields.get("issuetype", {}).get("name", "Task")
        task_type = self.REVERSE_TYPE_MAPPING.get(type_name, TaskType.TASK)

        # Assignee
        assignee = fields.get("assignee")
        assignee_id = assignee.get("accountId") if assignee else None

        # Due date
        due_date = None
        if fields.get("duedate"):
            try:
                due_date = datetime.strptime(fields["duedate"], "%Y-%m-%d")
            except ValueError:
                pass

        # Created/Updated dates
        created_at = datetime.fromisoformat(fields.get("created", "").replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(fields.get("updated", "").replace("Z", "+00:00"))

        return Task(
            id=jira_issue.get("id"),
            title=fields.get("summary", ""),
            description=description,
            task_type=task_type,
            priority=priority,
            status=status,
            assignee_id=assignee_id,
            department_id=department_id,
            jira_issue_key=jira_issue.get("key"),
            labels=fields.get("labels", []),
            created_at=created_at,
            updated_at=updated_at,
            due_date=due_date,
            source="jira",
        )

    def create(self, task: Task) -> Task:
        """Create a new task in Jira.
        
        Args:
            task: Task to create
            
        Returns:
            Created task with Jira issue key
        """
        logger.info(f"Creating task in Jira: {task.title}")

        jira_data = self._task_to_jira_format(task)
        result = self.client.create_issue(jira_data)

        # Update task with Jira data
        task.jira_issue_key = result.get("key")
        task.id = result.get("id")

        logger.info(f"Created Jira issue: {task.jira_issue_key}")
        return task

    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by Jira issue key.
        
        Args:
            task_id: Jira issue key (e.g., PROJ-123)
            
        Returns:
            Task if found, None otherwise
        """
        try:
            jira_issue = self.client.get_issue(task_id)
            # We need department_id - for now use empty string
            # In real implementation, get from task or project metadata
            return self._jira_to_task(jira_issue, "")
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None

    def update(self, task: Task) -> Task:
        """Update existing task in Jira.
        
        Args:
            task: Task with updated data
            
        Returns:
            Updated task
        """
        if not task.jira_issue_key:
            raise ValueError("Task must have jira_issue_key to update")

        logger.info(f"Updating Jira issue: {task.jira_issue_key}")

        # Create update payload
        update_data = self._task_to_jira_format(task)
        
        self.client.update_issue(task.jira_issue_key, update_data)
        
        logger.info(f"Updated Jira issue: {task.jira_issue_key}")
        return task

    def list_by_department(self, department_id: str) -> List[Task]:
        """List all tasks for a department.
        
        Args:
            department_id: Department identifier
            
        Returns:
            List of tasks
        """
        # In real implementation, filter by component or label
        jql = f"project = {self.project_key} AND labels = {department_id}"
        return self._search_tasks(jql, department_id)

    def list_by_sprint(self, sprint_id: str) -> List[Task]:
        """List all tasks in a sprint.
        
        Args:
            sprint_id: Sprint identifier
            
        Returns:
            List of tasks
        """
        jql = f"project = {self.project_key} AND sprint = {sprint_id}"
        return self._search_tasks(jql, "")

    def list_by_assignee(self, assignee_id: str) -> List[Task]:
        """List all tasks assigned to a user.
        
        Args:
            assignee_id: User Jira account ID
            
        Returns:
            List of tasks
        """
        jql = f"project = {self.project_key} AND assignee = {assignee_id}"
        return self._search_tasks(jql, "")

    def _search_tasks(self, jql: str, department_id: str) -> List[Task]:
        """Search tasks using JQL.
        
        Args:
            jql: JQL query
            department_id: Department ID for tasks
            
        Returns:
            List of tasks
        """
        try:
            results = self.client.search_issues(jql, max_results=100)
            tasks = []
            
            for issue in results.get("issues", []):
                task = self._jira_to_task(issue, department_id)
                tasks.append(task)
            
            logger.info(f"Found {len(tasks)} tasks for JQL: {jql}")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to search tasks: {e}")
            return []


