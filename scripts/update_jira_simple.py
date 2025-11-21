"""Simple update script - updates existing Jira tasks with Notion content.

This version uses simpler approach: manually specify task keys to update.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from src.infrastructure.notion.notion_storage import NotionStorage
from src.infrastructure.jira.jira_client import JiraClient

load_dotenv()
console = Console()


def main():
    """Update specific tasks."""
    console.print(Panel.fit(
        "[bold]Simple Jira Update[/bold]\n"
        "[dim]Update specific tasks with Notion content[/dim]",
        border_style="blue"
    ))
    
    # Configuration
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    # Load Notion data
    console.print("\n[blue]Loading Notion data...[/blue]")
    storage = NotionStorage()
    pages = storage.load_all_pages()
    console.print(f"[green]Loaded {len(pages)} pages[/green]")
    
    # Connect to Jira
    console.print("[blue]Connecting to Jira...[/blue]")
    client = JiraClient(jira_url, jira_email, jira_token)
    console.print("[green]Connected![/green]\n")
    
    # Example: Update task DG-150
    task_key = "DG-150"
    console.print(f"[cyan]Fetching {task_key}...[/cyan]")
    
    try:
        issue = client.get_issue(task_key)
        title = issue['fields']['summary']
        console.print(f"Task: {title}")
        
        # Find matching Notion page
        notion_page = None
        for page in pages:
            if page.get_title().lower().strip() == title.lower().strip():
                notion_page = page
                break
        
        if notion_page:
            console.print(f"[green]Found matching Notion page![/green]")
            console.print(f"  Blocks: {len(notion_page.blocks)}")
            console.print(f"  Todos: {len(notion_page.get_todo_items())}")
            console.print(f"  Images: {len(notion_page.get_images())}")
            
            # Build simple description
            desc_text = f"Описание задачи\\n\\n{notion_page.get_content_markdown()}"
            desc_text += f"\\n\\nОригинал: {notion_page.url}"
            
            console.print(f"\n[yellow]Description preview:[/yellow]")
            console.print(desc_text[:200] + "...")
            
        else:
            console.print(f"[red]No matching Notion page found[/red]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    client.close()
    console.print("\n[green]Done![/green]")


if __name__ == "__main__":
    main()







