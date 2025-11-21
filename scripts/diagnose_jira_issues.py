"""Diagnose Jira issues creation problems.

This script tests creating a single task to identify issues.
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
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv rich --quiet")
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.panel import Panel

from src.infrastructure.jira.jira_client import JiraClient

load_dotenv()
console = Console()


def test_jira_connection():
    """Test basic Jira connection and project access."""
    console.print(Panel.fit(
        "[bold]Jira Connection Diagnostics[/bold]",
        border_style="blue"
    ))
    
    # Get configuration
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")
    
    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"  JIRA_URL: {jira_url}")
    console.print(f"  JIRA_EMAIL: {jira_email}")
    console.print(f"  JIRA_PROJECT_KEY: {project_key}")
    console.print(f"  JIRA_API_TOKEN: {'*' * 20 if jira_token else 'NOT SET'}\n")
    
    if not all([jira_url, jira_email, jira_token, project_key]):
        console.print("[red]Error: Missing configuration![/red]")
        return False
    
    try:
        console.print("[blue]Connecting to Jira...[/blue]")
        client = JiraClient(jira_url, jira_email, jira_token)
        
        # Test 1: Get project
        console.print(f"\n[bold]Test 1: Get project '{project_key}'[/bold]")
        try:
            project = client.get_project(project_key)
            console.print(f"[green]Success![/green] Project: {project.get('name')}")
            console.print(f"  ID: {project.get('id')}")
            console.print(f"  Key: {project.get('key')}")
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            return False
        
        # Test 2: Get issue types
        console.print(f"\n[bold]Test 2: Get issue types for project[/bold]")
        try:
            # Get create metadata
            response = client._get(f"/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes.fields")
            
            if 'projects' in response and response['projects']:
                project_meta = response['projects'][0]
                issue_types = project_meta.get('issuetypes', [])
                
                console.print(f"[green]Available issue types:[/green]")
                for it in issue_types:
                    console.print(f"  - {it['name']} (id: {it['id']})")
                
                # Show required fields for Task
                task_type = next((it for it in issue_types if it['name'] == 'Task'), None)
                if task_type:
                    console.print(f"\n[bold]Required fields for 'Task':[/bold]")
                    fields = task_type.get('fields', {})
                    for field_id, field_info in fields.items():
                        if field_info.get('required'):
                            console.print(f"  - {field_info['name']} ({field_id})")
            else:
                console.print("[yellow]No project metadata found[/yellow]")
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
        
        # Test 3: Try creating a minimal test issue
        console.print(f"\n[bold]Test 3: Create test issue[/bold]")
        try:
            test_issue = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": "TEST - Diagnostic test issue (can be deleted)",
                    "issuetype": {"name": "Task"},
                    "description": "This is a test issue created by diagnostic script. You can safely delete it."
                }
            }
            
            console.print("[dim]Creating test issue...[/dim]")
            result = client.create_issue(test_issue)
            
            issue_key = result.get('key')
            console.print(f"[green]Success![/green] Created: {jira_url}/browse/{issue_key}")
            console.print(f"[yellow]Please delete this test issue: {issue_key}[/yellow]")
            
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
            console.print("\n[yellow]Detailed error:[/yellow]")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 4: Get assignable users
        console.print(f"\n[bold]Test 4: Get assignable users[/bold]")
        try:
            users = client.get_assignable_users(project_key)
            console.print(f"[green]Found {len(users)} assignable users:[/green]")
            for user in users[:5]:
                console.print(f"  - {user.get('displayName')} ({user.get('accountId')})")
            if len(users) > 5:
                console.print(f"  ... and {len(users) - 5} more")
        except Exception as e:
            console.print(f"[red]Failed: {e}[/red]")
        
        client.close()
        
        console.print("\n[bold green]All tests passed![/bold green]")
        return True
        
    except Exception as e:
        console.print(f"\n[red]Connection failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_jira_connection()
    sys.exit(0 if success else 1)







