"""Update all Jira tasks with Notion content by task range.

This script updates tasks DG-1 to DG-200 with full Notion content.
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

from src.infrastructure.notion.notion_storage import NotionStorage
from src.infrastructure.jira.jira_client import JiraClient

load_dotenv()
console = Console()


def build_adf_description(page) -> dict:
    """Build ADF description from Notion page."""
    content = []
    
    # Header
    content.append({
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": "Описание из Notion"}]
    })
    
    # Content
    page_content = page.get_content_markdown()
    if page_content and page_content.strip():
        paragraphs = [p for p in page_content.split('\n\n') if p.strip()]
        for para in paragraphs[:20]:  # Limit to 20 paragraphs
            if para.strip():
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": para.strip()[:1000]}]  # Limit length
                })
    
    # Todo items
    todos = page.get_todo_items()
    if todos:
        content.append({
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "Чеклист"}]
        })
        
        task_items = []
        for todo in todos[:50]:  # Limit to 50 items
            task_items.append({
                "type": "taskItem",
                "attrs": {"state": "DONE" if todo.checked else "TODO"},
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": todo.get_plain_text()[:500]}]
                }]
            })
        
        if task_items:
            content.append({
                "type": "taskList",
                "attrs": {"localId": "checklist-1"},
                "content": task_items
            })
    
    # Images
    images = page.get_images()
    if images:
        content.append({
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "Изображения"}]
        })
        
        for img in images[:10]:  # Limit to 10 images
            if img.file:
                content.append({
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "🖼️ "},
                        {
                            "type": "text",
                            "text": img.file.url[:200],
                            "marks": [{"type": "link", "attrs": {"href": img.file.url}}]
                        }
                    ]
                })
    
    # Links
    links = page.get_links()
    if links:
        unique_links = list(set(links))[:10]  # Limit to 10 links
        if unique_links:
            content.append({
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Ссылки"}]
            })
            
            for link in unique_links:
                content.append({
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "🔗 "},
                        {
                            "type": "text",
                            "text": link[:200],
                            "marks": [{"type": "link", "attrs": {"href": link}}]
                        }
                    ]
                })
    
    # Metadata
    content.append({"type": "rule"})
    content.append({
        "type": "paragraph",
        "content": [
            {"type": "text", "text": "Импортировано из Notion • ", "marks": [{"type": "em"}]},
            {
                "type": "text",
                "text": "Оригинал",
                "marks": [
                    {"type": "em"},
                    {"type": "link", "attrs": {"href": page.url}}
                ]
            }
        ]
    })
    
    return {
        "type": "doc",
        "version": 1,
        "content": content
    }


def main():
    """Update all tasks."""
    console.print(Panel.fit(
        "[bold]Update All Jira Tasks from Notion[/bold]\n"
        "[dim]Updating tasks with full content...[/dim]",
        border_style="blue"
    ))
    
    # Configuration
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY", "DG")
    
    # Settings
    dry_run = False  # Set to False to actually update
    start_num = 1
    end_num = 200
    
    console.print(f"\n[yellow]Settings:[/yellow]")
    console.print(f"  Project: {project_key}")
    console.print(f"  Range: {project_key}-{start_num} to {project_key}-{end_num}")
    console.print(f"  Dry run: {dry_run}\n")
    
    if dry_run:
        console.print("[bold yellow]DRY RUN MODE - No tasks will be updated[/bold yellow]\n")
    else:
        console.print("[bold green]REAL UPDATE MODE![/bold green]\n")
    
    # Load Notion data
    console.print("[blue]Loading Notion data...[/blue]")
    storage = NotionStorage()
    pages = storage.load_all_pages()
    console.print(f"[green]Loaded {len(pages)} pages[/green]\n")
    
    # Create title index
    title_index = {page.get_title().lower().strip(): page for page in pages}
    
    # Connect to Jira
    console.print("[blue]Connecting to Jira...[/blue]")
    client = JiraClient(jira_url, jira_email, jira_token)
    console.print("[green]Connected![/green]\n")
    
    # Update tasks
    updated = 0
    skipped = 0
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
                # Get task from Jira
                issue = client.get_issue(task_key)
                title = issue['fields']['summary']
                
                # Find matching Notion page
                notion_page = title_index.get(title.lower().strip())
                
                if not notion_page:
                    skipped += 1
                    progress.advance(task)
                    continue
                
                if dry_run:
                    console.print(f"[dim]Would update {task_key}: {title[:50]}...[/dim]")
                    updated += 1
                else:
                    # Build description
                    description = build_adf_description(notion_page)
                    
                    # Update labels
                    labels = issue['fields'].get('labels', [])
                    new_labels = ['full-content-updated']
                    if notion_page.get_todo_items():
                        new_labels.append('has-checklist')
                    if notion_page.get_images():
                        new_labels.append('has-images')
                    
                    # Merge labels
                    all_labels = list(set(labels + new_labels))
                    
                    # Update
                    update_data = {
                        "fields": {
                            "description": description,
                            "labels": all_labels
                        }
                    }
                    
                    client.update_issue(task_key, update_data)
                    console.print(f"[green]✓ Updated {task_key}[/green]")
                    updated += 1
                    
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "not found" in error_msg.lower():
                    not_found += 1
                else:
                    console.print(f"[red]Error updating {task_key}: {e}[/red]")
                    errors += 1
            
            progress.advance(task)
    
    # Summary
    console.print("\n[bold blue]Update Summary[/bold blue]\n")
    console.print(f"  [green]Updated: {updated}[/green]")
    console.print(f"  [yellow]Skipped (no match): {skipped}[/yellow]")
    console.print(f"  [dim]Not found: {not_found}[/dim]")
    console.print(f"  [red]Errors: {errors}[/red]")
    
    if dry_run:
        console.print("\n[yellow]DRY RUN: No tasks were actually updated[/yellow]")
        console.print("[bold]To update:[/bold] Set dry_run=False in the script")
    else:
        console.print(f"\n[bold green]✓ Updated {updated} tasks![/bold green]")
    
    client.close()


if __name__ == "__main__":
    main()

