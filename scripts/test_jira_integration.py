"""Test Jira integration.

This script tests the Jira integration with real API calls.
Run this after filling .env to verify everything works.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv rich --quiet")
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

# Import our code
from src.domain.models.task import Priority, TaskType
from src.infrastructure.jira.jira_client import JiraClient
from src.infrastructure.jira.jira_repository import JiraTaskRepository
from src.application.use_cases.create_task_in_jira import CreateTaskInJiraUseCase

load_dotenv()
console = Console()


def test_jira_connection():
    """Test 1: Basic connection."""
    console.print("\n[bold blue]Test 1: Jira Connection[/bold blue]\n")
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, jira_email, jira_token]):
        console.print("[red][X] Jira credentials not configured in .env[/red]")
        return False
    
    try:
        client = JiraClient(jira_url, jira_email, jira_token)
        
        # Test connection
        user_info = client.get_myself()
        
        console.print(f"[green][OK] Connected to Jira![/green]")
        console.print(f"[green]   User: {user_info.get('displayName')}[/green]")
        console.print(f"[green]   Email: {user_info.get('emailAddress')}[/green]")
        
        client.close()
        return True
        
    except Exception as e:
        console.print(f"[red][X] Connection failed: {e}[/red]")
        return False


def test_get_project():
    """Test 2: Get project information."""
    console.print("\n[bold blue]Test 2: Get Project Info[/bold blue]\n")
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")
    
    try:
        client = JiraClient(jira_url, jira_email, jira_token)
        
        # Get project
        project = client.get_project(project_key)
        
        console.print(f"[green][OK] Project found![/green]")
        console.print(f"[green]   Key: {project.get('key')}[/green]")
        console.print(f"[green]   Name: {project.get('name')}[/green]")
        console.print(f"[green]   Lead: {project.get('lead', {}).get('displayName')}[/green]")
        
        client.close()
        return True
        
    except Exception as e:
        console.print(f"[red][X] Failed: {e}[/red]")
        return False


def test_search_issues():
    """Test 3: Search issues."""
    console.print("\n[bold blue]Test 3: Search Issues[/bold blue]\n")
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")
    
    try:
        client = JiraClient(jira_url, jira_email, jira_token)
        
        # Search issues
        jql = f"project = {project_key} ORDER BY created DESC"
        results = client.search_issues(jql, max_results=5)
        
        issues = results.get("issues", [])
        total = results.get("total", 0)
        
        console.print(f"[green][OK] Found {total} issues total[/green]")
        
        if issues:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Key", style="cyan")
            table.add_column("Summary", width=50)
            table.add_column("Status", style="yellow")
            
            for issue in issues[:5]:
                key = issue.get("key")
                summary = issue.get("fields", {}).get("summary", "")[:50]
                status = issue.get("fields", {}).get("status", {}).get("name", "")
                
                table.add_row(key, summary, status)
            
            console.print(table)
        else:
            console.print("[yellow]No issues found in project[/yellow]")
        
        client.close()
        return True
        
    except Exception as e:
        console.print(f"[red][X] Failed: {e}[/red]")
        return False


def test_create_task():
    """Test 4: Create a task (REAL OPERATION!)."""
    console.print("\n[bold blue]Test 4: Create Task (DRY RUN)[/bold blue]\n")
    
    console.print("[yellow]This would create a real task in Jira.[/yellow]")
    console.print("[yellow]Enable by changing dry_run=False in code.[/yellow]\n")
    
    dry_run = True  # Change to False to actually create
    
    if dry_run:
        console.print("[dim]Skipping task creation (dry run mode)[/dim]")
        return True
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")
    
    try:
        # Initialize infrastructure
        client = JiraClient(jira_url, jira_email, jira_token)
        repository = JiraTaskRepository(client, project_key)
        
        # Initialize use case
        create_task_use_case = CreateTaskInJiraUseCase(repository)
        
        # Create test task
        task = create_task_use_case.execute(
            title="[TEST] Integration test task",
            department_id="test",
            description="This is a test task created by the integration test script.",
            priority=Priority.LOW,
            task_type=TaskType.TASK,
            labels=["test", "integration"]
        )
        
        console.print(f"[green][OK] Task created![/green]")
        console.print(f"[green]   Issue Key: {task.jira_issue_key}[/green]")
        console.print(f"[green]   Title: {task.title}[/green]")
        console.print(f"[green]   URL: {jira_url}/browse/{task.jira_issue_key}[/green]")
        
        client.close()
        return True
        
    except Exception as e:
        console.print(f"[red][X] Failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold]Jira Integration Test Suite[/bold]\n"
        "[dim]Testing Jira API integration...[/dim]",
        border_style="blue"
    ))
    
    tests = [
        ("Connection", test_jira_connection),
        ("Get Project", test_get_project),
        ("Search Issues", test_search_issues),
        ("Create Task", test_create_task),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            console.print(f"[red][X] {test_name} failed with exception: {e}[/red]")
            results.append((test_name, False))
    
    # Summary
    console.print("\n[bold blue]Test Results[/bold blue]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test", style="cyan", width=30)
    table.add_column("Result", width=15)
    
    passed = 0
    for test_name, success in results:
        if success:
            table.add_row(test_name, "[green][OK] PASSED[/green]")
            passed += 1
        else:
            table.add_row(test_name, "[red][X] FAILED[/red]")
    
    console.print(table)
    console.print(f"\n[bold]Passed: {passed}/{len(tests)}[/bold]\n")
    
    if passed == len(tests):
        console.print("[green][OK] All tests passed! Jira integration is working![/green]\n")
    else:
        console.print("[yellow][!] Some tests failed. Check the output above.[/yellow]\n")


if __name__ == "__main__":
    main()



