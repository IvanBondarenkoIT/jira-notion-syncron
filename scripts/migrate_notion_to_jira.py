"""Migrate tasks from Notion to Jira.

This script:
1. Reads tasks from Notion database
2. Maps users (default to DimKava if not sure)
3. Creates corresponding tasks in Jira
4. Shows progress and summary
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv requests rich --quiet")
    from dotenv import load_dotenv
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn

from src.infrastructure.jira.jira_client import JiraClient
from src.infrastructure.jira.jira_repository import JiraTaskRepository
from src.domain.models.task import Priority, TaskType
from src.application.use_cases.create_task_in_jira import CreateTaskInJiraUseCase

load_dotenv()
console = Console()

# Default assignee (DimKava)
DEFAULT_ASSIGNEE_ID = "712020:3bcced1b-9ddd-488d-b6fd-e0e8fc0e97a3"

# User mapping (Notion name -> Jira Account ID)
USER_MAPPING = {
    "Ivan": "712020:c40dface-b447-489f-865f-bf7b9ac9db3b",  # Ivan Bondarenko
    "Sasha SW": DEFAULT_ASSIGNEE_ID,  # Саша (using DimKava for now)
    "Sasha": DEFAULT_ASSIGNEE_ID,  # Саша
    "Anastasiia": "5ee270d1f557470aba0bb722",  # Анастасия Демихова
    "Nastya": "5ee270d1f557470aba0bb722",  # Анастасия Демихова
    "Nini": DEFAULT_ASSIGNEE_ID,  # Нини (using DimKava for now)
    "alex fedorov": "61e6b99b78cb6900714753ae",  # alex fedorov
    "Elana Fedorova": DEFAULT_ASSIGNEE_ID,  # Unknown (using DimKava)
    "DimKava": DEFAULT_ASSIGNEE_ID,
}


def get_notion_database(database_id: str, notion_token: str) -> List[Dict]:
    """Get all pages from Notion database."""
    console.print(f"[blue]Fetching data from Notion database...[/blue]\n")
    
    try:
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        all_results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            body = {}
            if start_cursor:
                body["start_cursor"] = start_cursor
            
            response = requests.post(url, headers=headers, json=body, timeout=30)
            
            if response.status_code != 200:
                console.print(f"[red]Error: {response.status_code}[/red]")
                console.print(f"[red]{response.text[:500]}[/red]")
                return []
            
            data = response.json()
            results = data.get("results", [])
            all_results.extend(results)
            
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        
        console.print(f"[green]Found {len(all_results)} pages in Notion[/green]\n")
        return all_results
        
    except Exception as e:
        console.print(f"[red]Error fetching Notion data: {e}[/red]")
        import traceback
        traceback.print_exc()
        return []


def parse_notion_page(page: Dict) -> Optional[Dict]:
    """Parse Notion page to task data."""
    try:
        properties = page.get("properties", {})
        
        # Title - "Task name" property
        title = ""
        title_prop = properties.get("Task name") or properties.get("Name") or properties.get("Title")
        if title_prop:
            title_content = title_prop.get("title", [])
            if title_content:
                title = title_content[0].get("plain_text", "")
        
        if not title or title.strip() == "":
            return None  # Skip pages without title
        
        # Status
        status = ""
        status_prop = properties.get("Status")
        if status_prop and status_prop.get("status"):
            status = status_prop.get("status", {}).get("name", "")
        
        # Assignee - property without name (people type)
        assignee = ""
        # Try all properties to find people type
        for prop_name, prop_value in properties.items():
            if prop_value.get("type") == "people":
                people = prop_value.get("people", [])
                if people:
                    # Join all assignees
                    assignees = [p.get("name", "") for p in people if p.get("name")]
                    assignee = assignees[0] if assignees else ""
                break
        
        # Priority
        priority = ""
        priority_prop = properties.get("Priority")
        if priority_prop and priority_prop.get("select"):
            priority = priority_prop.get("select", {}).get("name", "")
        
        # Description - we'll construct from available data
        description_parts = []
        
        # Add effort level if available
        effort_prop = properties.get("Effort level")
        if effort_prop and effort_prop.get("select"):
            effort = effort_prop.get("select", {}).get("name", "")
            if effort:
                description_parts.append(f"Effort level: {effort}")
        
        description = "\n".join(description_parts) if description_parts else ""
        
        # Due date
        due_date = ""
        due_prop = properties.get("Due date") or properties.get("Date")
        if due_prop and due_prop.get("date"):
            due_date = due_prop.get("date", {}).get("start", "")
        
        # Tags - "Task type" multi-select
        tags = []
        tags_prop = properties.get("Task type")
        if tags_prop and tags_prop.get("multi_select"):
            tags = [tag.get("name") for tag in tags_prop.get("multi_select", [])]
        
        return {
            "title": title.strip(),
            "status": status,
            "assignee": assignee,
            "priority": priority,
            "description": description,
            "due_date": due_date,
            "tags": tags,
            "notion_url": page.get("url", "")
        }
        
    except Exception as e:
        console.print(f"[yellow]Error parsing page: {e}[/yellow]")
        import traceback
        traceback.print_exc()
        return None


def map_priority(notion_priority: str) -> Priority:
    """Map Notion priority to Jira priority."""
    priority_lower = notion_priority.lower()
    
    if any(word in priority_lower for word in ["critical", "urgent", "критичный", "срочный"]):
        return Priority.CRITICAL
    elif any(word in priority_lower for word in ["high", "важный", "высокий"]):
        return Priority.HIGH
    elif any(word in priority_lower for word in ["low", "низкий"]):
        return Priority.LOW
    else:
        return Priority.MEDIUM


def get_jira_account_id(assignee_name: str) -> str:
    """Get Jira Account ID for assignee."""
    if not assignee_name:
        return DEFAULT_ASSIGNEE_ID
    
    # Check direct mapping
    if assignee_name in USER_MAPPING and USER_MAPPING[assignee_name]:
        return USER_MAPPING[assignee_name]
    
    # Check partial matches
    for key, value in USER_MAPPING.items():
        if key.lower() in assignee_name.lower() and value:
            return value
    
    # Default to DimKava
    console.print(f"[yellow]Unknown assignee '{assignee_name}', using DimKava[/yellow]")
    return DEFAULT_ASSIGNEE_ID


def create_jira_task(task_data: Dict, use_case: CreateTaskInJiraUseCase, dry_run: bool = True) -> Optional[str]:
    """Create task in Jira."""
    try:
        title = task_data["title"]
        
        # Build description with Notion info
        description_parts = []
        
        if task_data.get("description"):
            description_parts.append(task_data["description"])
        
        description_parts.append(f"\n---\nИмпортировано из Notion")
        
        if task_data.get("notion_url"):
            description_parts.append(f"Оригинал: {task_data['notion_url']}")
        
        if task_data.get("status"):
            description_parts.append(f"Статус в Notion: {task_data['status']}")
        
        description = "\n".join(description_parts)
        
        # Get assignee
        assignee_id = get_jira_account_id(task_data.get("assignee", ""))
        
        # Map priority
        priority = map_priority(task_data.get("priority", ""))
        
        # Labels
        labels = task_data.get("tags", [])
        labels.append("notion-import")
        
        if dry_run:
            console.print(f"[dim]Would create: {title}[/dim]")
            return None
        
        # Create task
        task = use_case.execute(
            title=title,
            department_id="general",
            description=description,
            assignee_id=assignee_id,
            priority=priority,
            task_type=TaskType.TASK,
            labels=labels
        )
        
        return task.jira_issue_key
        
    except Exception as e:
        console.print(f"[red]Error creating task '{task_data.get('title', 'Unknown')}': {e}[/red]")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main migration function."""
    console.print(Panel.fit(
        "[bold]Notion to Jira Migration[/bold]\n"
        "[dim]Migrating tasks from Notion to Jira...[/dim]",
        border_style="blue"
    ))
    
    # Check configuration
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db_id = os.getenv("NOTION_DATABASE_ID")
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")
    
    if not all([notion_token, notion_db_id]):
        console.print("[red]Error: Notion credentials not configured in .env[/red]")
        console.print("[yellow]Add NOTION_TOKEN and NOTION_DATABASE_ID to .env[/yellow]")
        return
    
    if not all([jira_url, jira_email, jira_token, project_key]):
        console.print("[red]Error: Jira credentials not configured in .env[/red]")
        return
    
    # REAL MIGRATION MODE
    console.print("\n[bold green]REAL MIGRATION MODE - Creating tasks in Jira![/bold green]")
    console.print("This will create actual tasks in Jira project\n")
    dry_run = False  # Set to True for dry-run mode
    
    # Get Notion data
    notion_pages = get_notion_database(notion_db_id, notion_token)
    
    if not notion_pages:
        console.print("[yellow]No pages found in Notion database[/yellow]")
        return
    
    # Parse pages
    console.print("[blue]Parsing Notion pages...[/blue]\n")
    tasks = []
    
    for page in notion_pages:
        task_data = parse_notion_page(page)
        if task_data:
            tasks.append(task_data)
    
    console.print(f"[green]Parsed {len(tasks)} valid tasks[/green]\n")
    
    if not tasks:
        console.print("[yellow]No valid tasks to import[/yellow]")
        return
    
    # Show preview
    console.print("[bold blue]Tasks to import:[/bold blue]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=5)
    table.add_column("Title", width=40)
    table.add_column("Assignee", style="green", width=15)
    table.add_column("Priority", style="yellow", width=10)
    table.add_column("Tags", width=20)
    
    for idx, task in enumerate(tasks[:10], 1):  # Show first 10
        table.add_row(
            str(idx),
            task["title"][:40],
            task.get("assignee", "DimKava")[:15],
            task.get("priority", "Medium"),
            ", ".join(task.get("tags", []))[:20]
        )
    
    if len(tasks) > 10:
        table.add_row("...", f"... and {len(tasks) - 10} more", "", "", "")
    
    console.print(table)
    
    # Initialize Jira
    console.print(f"\n[blue]Connecting to Jira...[/blue]")
    
    try:
        jira_client = JiraClient(jira_url, jira_email, jira_token)
        jira_repository = JiraTaskRepository(jira_client, project_key)
        use_case = CreateTaskInJiraUseCase(jira_repository)
        
        console.print(f"[green]Connected to Jira project: {project_key}[/green]\n")
        
        # Create tasks
        if dry_run:
            console.print("[bold yellow]DRY RUN - No tasks will be created[/bold yellow]\n")
        else:
            console.print("[bold green]Creating tasks in Jira...[/bold green]\n")
        
        created_keys = []
        failed_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task_progress = progress.add_task(
                f"[cyan]Processing {len(tasks)} tasks...",
                total=len(tasks)
            )
            
            for task_data in tasks:
                result = create_jira_task(task_data, use_case, dry_run)
                
                if result:
                    created_keys.append(result)
                elif not dry_run:
                    failed_count += 1
                
                progress.advance(task_progress)
        
        # Summary
        console.print("\n[bold blue]Migration Summary[/bold blue]\n")
        
        if dry_run:
            console.print(f"[yellow]DRY RUN: Would create {len(tasks)} tasks[/yellow]")
            console.print("\n[bold]To actually create tasks:[/bold]")
            console.print("1. Set dry_run=False in the script")
            console.print("2. Run the script again")
        else:
            console.print(f"[green]Successfully created: {len(created_keys)} tasks[/green]")
            console.print(f"[red]Failed: {failed_count} tasks[/red]")
            
            if created_keys:
                console.print("\n[bold]Created issues:[/bold]")
                for key in created_keys[:10]:
                    console.print(f"  - {jira_url}/browse/{key}")
                
                if len(created_keys) > 10:
                    console.print(f"  ... and {len(created_keys) - 10} more")
        
        jira_client.close()
        
    except Exception as e:
        console.print(f"\n[red]Migration failed: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

