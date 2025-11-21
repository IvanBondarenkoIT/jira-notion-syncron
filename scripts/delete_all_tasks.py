"""Delete all tasks from Jira project.

WARNING: This is IRREVERSIBLE operation!
Use with caution.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

from src.infrastructure.jira.jira_client import JiraClient

load_dotenv()
console = Console()


def main():
    """Delete all tasks from project."""
    console.print(Panel.fit(
        "[bold red]WARNING: DELETE ALL TASKS[/bold red]\n"
        "[yellow]This will delete ALL tasks from the project![/yellow]",
        border_style="red"
    ))
    
    # Configuration
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY", "DG")
    
    # Settings
    dry_run = False  # Set to False to actually delete
    start_num = 1
    end_num = 200
    
    console.print(f"\n[yellow]Settings:[/yellow]")
    console.print(f"  Project: {project_key}")
    console.print(f"  Range: {project_key}-{start_num} to {project_key}-{end_num}")
    console.print(f"  Dry run: {dry_run}\n")
    
    if dry_run:
        console.print("[bold yellow]DRY RUN MODE - No tasks will be deleted[/bold yellow]\n")
    else:
        console.print("[bold red]REAL DELETE MODE - THIS IS IRREVERSIBLE![/bold red]\n")
        
        # Skip confirmation - user already confirmed
        console.print("[yellow]User confirmed deletion. Proceeding...[/yellow]\n")
    
    # Connect to Jira
    console.print("[blue]Connecting to Jira...[/blue]")
    client = JiraClient(jira_url, jira_email, jira_token)
    console.print("[green]Connected![/green]\n")
    
    # Delete tasks
    deleted = 0
    not_found = 0
    errors = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(
            f"[cyan]Processing {end_num - start_num + 1} tasks...",
            total=end_num - start_num + 1
        )
        
        for num in range(start_num, end_num + 1):
            task_key = f"{project_key}-{num}"
            
            try:
                # Check if task exists
                issue = client.get_issue(task_key)
                title = issue['fields']['summary']
                
                if dry_run:
                    console.print(f"[dim]Would delete {task_key}: {title[:50]}...[/dim]")
                    deleted += 1
                else:
                    # Delete task
                    client._delete(f"/rest/api/3/issue/{task_key}")
                    console.print(f"[red]Deleted {task_key}: {title[:50]}[/red]")
                    deleted += 1
                    
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "not found" in error_msg.lower():
                    not_found += 1
                else:
                    console.print(f"[red]Error deleting {task_key}: {e}[/red]")
                    errors += 1
            
            progress.advance(task)
    
    # Summary
    console.print("\n[bold blue]Deletion Summary[/bold blue]\n")
    console.print(f"  [red]Deleted: {deleted}[/red]")
    console.print(f"  [dim]Not found: {not_found}[/dim]")
    console.print(f"  [yellow]Errors: {errors}[/yellow]")
    
    if dry_run:
        console.print("\n[yellow]DRY RUN: No tasks were actually deleted[/yellow]")
        console.print("[bold]To delete:[/bold] Set dry_run=False in the script")
    else:
        console.print(f"\n[bold red]Deleted {deleted} tasks![/bold red]")
        console.print("\n[green]You can now run the migration script to recreate tasks with full content.[/green]")
    
    client.close()


if __name__ == "__main__":
    main()

