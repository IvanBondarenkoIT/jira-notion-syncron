"""Jira API client.

Low-level client for interacting with Jira REST API.
Handles authentication, requests, and error handling.
"""

import logging
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class JiraClientError(Exception):
    """Base exception for Jira client errors."""

    pass


class JiraAuthenticationError(JiraClientError):
    """Raised when authentication fails."""

    pass


class JiraNotFoundError(JiraClientError):
    """Raised when resource is not found."""

    pass


class JiraClient:
    """Low-level Jira API client.
    
    Handles HTTP requests to Jira REST API v3.
    
    Attributes:
        base_url: Jira instance URL
        auth: HTTP Basic authentication
        session: Requests session for connection pooling
    """

    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        """Initialize Jira client.
        
        Args:
            base_url: Jira instance URL (e.g., https://your-domain.atlassian.net)
            email: User email for authentication
            api_token: Jira API token
        """
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        logger.info(f"Initialized Jira client for {self.base_url}")

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to Jira API.
        
        Args:
            endpoint: API endpoint (e.g., /rest/api/3/issue/PROJ-123)
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            JiraAuthenticationError: If authentication fails
            JiraNotFoundError: If resource not found
            JiraClientError: For other errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 401:
                raise JiraAuthenticationError("Authentication failed - check email and API token")
            elif response.status_code == 404:
                raise JiraNotFoundError(f"Resource not found: {endpoint}")
            elif response.status_code >= 400:
                raise JiraClientError(
                    f"Jira API error: {response.status_code} - {response.text[:200]}"
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise JiraClientError(f"Request timeout for {url}")
        except requests.exceptions.ConnectionError:
            raise JiraClientError(f"Connection error for {url}")
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Request failed: {str(e)}")

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to Jira API.
        
        Args:
            endpoint: API endpoint
            data: Request body as dictionary
            
        Returns:
            JSON response as dictionary
            
        Raises:
            JiraAuthenticationError: If authentication fails
            JiraClientError: For other errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code == 401:
                raise JiraAuthenticationError("Authentication failed - check email and API token")
            elif response.status_code >= 400:
                raise JiraClientError(
                    f"Jira API error: {response.status_code} - {response.text[:500]}"
                )
            
            response.raise_for_status()
            
            # Some endpoints return 201 Created with location header
            if response.status_code == 201:
                return response.json() if response.content else {}
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise JiraClientError(f"Request timeout for {url}")
        except requests.exceptions.ConnectionError:
            raise JiraClientError(f"Connection error for {url}")
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Request failed: {str(e)}")

    def _put(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make PUT request to Jira API.
        
        Args:
            endpoint: API endpoint
            data: Request body as dictionary
            
        Returns:
            JSON response as dictionary or None
            
        Raises:
            JiraAuthenticationError: If authentication fails
            JiraClientError: For other errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.put(url, json=data, timeout=30)
            
            if response.status_code == 401:
                raise JiraAuthenticationError("Authentication failed")
            elif response.status_code >= 400:
                raise JiraClientError(
                    f"Jira API error: {response.status_code} - {response.text[:500]}"
                )
            
            response.raise_for_status()
            
            # PUT often returns 204 No Content
            return response.json() if response.content else None
            
        except requests.exceptions.Timeout:
            raise JiraClientError(f"Request timeout for {url}")
        except requests.exceptions.ConnectionError:
            raise JiraClientError(f"Connection error for {url}")
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Request failed: {str(e)}")
    
    def _delete(self, endpoint: str) -> None:
        """Make DELETE request to Jira API.
        
        Args:
            endpoint: API endpoint
            
        Raises:
            JiraAuthenticationError: If authentication fails
            JiraClientError: For other errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.delete(url, timeout=30)
            
            if response.status_code == 401:
                raise JiraAuthenticationError("Authentication failed")
            elif response.status_code >= 400:
                raise JiraClientError(
                    f"Jira API error: {response.status_code} - {response.text[:500]}"
                )
            
            response.raise_for_status()
            
        except requests.exceptions.Timeout:
            raise JiraClientError(f"Request timeout for {url}")
        except requests.exceptions.ConnectionError:
            raise JiraClientError(f"Connection error for {url}")
        except requests.exceptions.RequestException as e:
            raise JiraClientError(f"Request failed: {str(e)}")

    def get_myself(self) -> Dict[str, Any]:
        """Get current user information.
        
        Returns:
            User information dictionary
        """
        return self._get("/rest/api/3/myself")

    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Get issue by key.
        
        Args:
            issue_key: Issue key (e.g., PROJ-123)
            
        Returns:
            Issue data dictionary
        """
        logger.info(f"Fetching issue: {issue_key}")
        return self._get(f"/rest/api/3/issue/{issue_key}")

    def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue.
        
        Args:
            issue_data: Issue data dictionary following Jira API format
            
        Returns:
            Created issue data with key and ID
            
        Example:
            >>> issue_data = {
            ...     "fields": {
            ...         "project": {"key": "PROJ"},
            ...         "summary": "Task title",
            ...         "description": {...},
            ...         "issuetype": {"name": "Task"}
            ...     }
            ... }
            >>> result = client.create_issue(issue_data)
        """
        logger.info(f"Creating issue in project: {issue_data.get('fields', {}).get('project', {}).get('key')}")
        
        # Convert description to ADF format if it's plain text
        if "fields" in issue_data and "description" in issue_data["fields"]:
            desc = issue_data["fields"]["description"]
            if isinstance(desc, str):
                # Convert plain text to ADF format
                issue_data["fields"]["description"] = self._text_to_adf(desc)
        
        return self._post("/rest/api/3/issue", issue_data)

    def update_issue(self, issue_key: str, update_data: Dict[str, Any]) -> None:
        """Update an existing issue.
        
        Args:
            issue_key: Issue key (e.g., PROJ-123)
            update_data: Update data dictionary
        """
        logger.info(f"Updating issue: {issue_key}")
        self._put(f"/rest/api/3/issue/{issue_key}", update_data)

    def search_issues(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 50,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search issues using JQL.
        
        Args:
            jql: JQL query string
            start_at: Starting index for pagination
            max_results: Maximum number of results
            fields: List of fields to return (None = all fields)
            
        Returns:
            Search results with issues list
            
        Example:
            >>> results = client.search_issues(
            ...     jql="project = PROJ AND status = 'In Progress'",
            ...     max_results=10
            ... )
        """
        logger.info(f"Searching issues with JQL: {jql}")
        
        body: Dict[str, Any] = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }
        
        if fields:
            body["fields"] = fields
        
        # Use the new search/jql endpoint with POST
        result = self._post("/rest/api/3/search/jql", body)
        
        # Return in expected format
        return {
            "issues": result.get("values", []),
            "total": result.get("total", 0),
            "startAt": result.get("startAt", 0),
            "maxResults": result.get("maxResults", max_results)
        }

    def get_project(self, project_key: str) -> Dict[str, Any]:
        """Get project information.
        
        Args:
            project_key: Project key (e.g., PROJ)
            
        Returns:
            Project data dictionary
        """
        logger.info(f"Fetching project: {project_key}")
        return self._get(f"/rest/api/3/project/{project_key}")

    def get_board(self, board_id: int) -> Dict[str, Any]:
        """Get Agile board information.
        
        Args:
            board_id: Board ID
            
        Returns:
            Board data dictionary
        """
        logger.info(f"Fetching board: {board_id}")
        return self._get(f"/rest/agile/1.0/board/{board_id}")

    def get_sprints(self, board_id: int, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sprints for a board.
        
        Args:
            board_id: Board ID
            state: Sprint state filter (active, future, closed)
            
        Returns:
            List of sprint dictionaries
        """
        logger.info(f"Fetching sprints for board: {board_id}")
        
        params = {}
        if state:
            params["state"] = state
        
        response = self._get(f"/rest/agile/1.0/board/{board_id}/sprint", params=params)
        return response.get("values", [])

    def create_sprint(
        self,
        board_id: int,
        name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new sprint.
        
        Args:
            board_id: Board ID
            name: Sprint name
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            Created sprint data
        """
        logger.info(f"Creating sprint: {name} on board {board_id}")
        
        sprint_data = {
            "name": name,
            "originBoardId": board_id
        }
        
        if start_date:
            sprint_data["startDate"] = start_date
        if end_date:
            sprint_data["endDate"] = end_date
        
        return self._post("/rest/agile/1.0/sprint", sprint_data)
    
    def _text_to_adf(self, text: str) -> Dict[str, Any]:
        """Convert plain text to Atlassian Document Format (ADF).
        
        Args:
            text: Plain text description
            
        Returns:
            ADF document structure
        """
        if not text or text.strip() == "":
            return {
                "type": "doc",
                "version": 1,
                "content": []
            }
        
        # Split by paragraphs (double newlines)
        paragraphs = text.split('\n\n')
        
        content = []
        for para in paragraphs:
            para = para.strip()
            if para:
                # Split lines within paragraph
                lines = para.split('\n')
                para_content = []
                
                for i, line in enumerate(lines):
                    if line.strip():
                        para_content.append({
                            "type": "text",
                            "text": line
                        })
                        # Add line break if not last line
                        if i < len(lines) - 1:
                            para_content.append({
                                "type": "hardBreak"
                            })
                
                if para_content:
                    content.append({
                        "type": "paragraph",
                        "content": para_content
                    })
        
        # If no content, add single paragraph with text
        if not content:
            content = [{
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": text
                }]
            }]
        
        return {
            "type": "doc",
            "version": 1,
            "content": content
        }

    def close(self) -> None:
        """Close the client session."""
        self.session.close()
        logger.info("Jira client session closed")

    def __enter__(self) -> "JiraClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

