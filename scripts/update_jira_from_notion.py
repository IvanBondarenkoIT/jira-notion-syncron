"""Update existing Jira tasks with full content from Notion.

This script:
1. Finds existing tasks in Jira (imported from Notion)
2. Loads full content from local Notion export
3. Updates Jira task descriptions with complete content
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv rich --quiet")
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn

from src.infrastructure.notion.notion_storage import NotionStorage
from src.infrastructure.jira.jira_client import JiraClient
from src.domain.models.notion_block import NotionPage

load_dotenv()
console = Console()


def build_rich_description_adf(page: NotionPage) -> Dict:
    """Build rich Jira description from Notion page in ADF format.
    
    Args:
        page: NotionPage with full content
        
    Returns:
        ADF document
    """
    content = []
    
    # Header
    content.append({
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": "Описание задачи"}]
    })
    
    # Main content
    page_content = page.get_content_markdown()
    if page_content and page_content.strip():
        # Split into paragraphs
        paragraphs = page_content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": para.strip()}]
                })
    
    # Todo items (checklist)
    todos = page.get_todo_items()
    if todos:
        content.append({
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "Чеклист"}]
        })
        
        # Create task list
        task_items = []
        for todo in todos:
            task_items.append({
                "type": "taskItem",
                "attrs": {"state": "DONE" if todo.checked else "TODO"},
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": todo.get_plain_text()}]
                    }
                ]
            })
        
        content.append({
            "type": "taskList",
            "attrs": {"localId": "task-list-1"},
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
        
        for img in images:
            if img.file:
                # Add image
                content.append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "📷 Изображение: "
                        },
                        {
                            "type": "text",
                            "text": img.file.url,
                            "marks": [{"type": "link", "attrs": {"href": img.file.url}}]
                        }
                    ]
                })
                
                # Caption if exists
                caption = img.get_caption_text()
                if caption:
                    content.append({
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": f"_{caption}_",
                                "marks": [{"type": "em"}]
                            }
                        ]
                    })
    
    # Files
    files = page.get_files()
    if files:
        content.append({
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": "Файлы"}]
        })
        
        for file in files:
            if file.file:
                name = file.file.name or "Файл"
                content.append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "📎 "
                        },
                        {
                            "type": "text",
                            "text": name,
                            "marks": [{"type": "link", "attrs": {"href": file.file.url}}]
                        }
                    ]
                })
    
    # Links
    links = page.get_links()
    if links:
        unique_links = list(set(links))
        if unique_links:
            content.append({
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Ссылки"}]
            })
            
            for link in unique_links[:10]:  # Limit to 10 links
                content.append({
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "🔗 "
                        },
                        {
                            "type": "text",
                            "text": link,
                            "marks": [{"type": "link", "attrs": {"href": link}}]
                        }
                    ]
                })
    
    # Divider
    content.append({"type": "rule"})
    
    # Metadata
    content.append({
        "type": "heading",
        "attrs": {"level": 3},
        "content": [{"type": "text", "text": "Метаданные"}]
    })
    
    # Get properties
    status = page.get_property_value("Status")
    priority = page.get_property_value("Priority")
    effort = page.get_property_value("Effort level")
    due_date = page.get_property_value("Due date")
    tags = page.get_property_value("Task type")
    
    metadata_items = []
    if status:
        metadata_items.append(f"Статус в Notion: {status}")
    if priority:
        metadata_items.append(f"Приоритет: {priority}")
    if effort:
        metadata_items.append(f"Уровень усилий: {effort}")
    if due_date:
        metadata_items.append(f"Срок: {due_date}")
    if tags:
        if isinstance(tags, list):
            metadata_items.append(f"Теги: {', '.join(tags)}")
        else:
            metadata_items.append(f"Теги: {tags}")
    
    for item in metadata_items:
        content.append({
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": item,
                    "marks": [{"type": "strong"}]
                }
            ]
        })
    
    # Notion link
    content.append({
        "type": "paragraph",
        "content": [
            {
                "type": "text",
                "text": "Оригинал в Notion: ",
                "marks": [{"type": "strong"}]
            },
            {
                "type": "text",
                "text": page.url,
                "marks": [{"type": "link", "attrs": {"href": page.url}}]
            }
        ]
    })
    
    content.append({
        "type": "paragraph",
        "content": [
            {
                "type": "text",
                "text": f"Обновлено: {page.last_edited_time.strftime('%Y-%m-%d %H:%M')}",
                "marks": [{"type": "strong"}]
            }
        ]
    })
    
    return {
        "type": "doc",
        "version": 1,
        "content": content
    }


def find_notion_page_by_title(pages: List[NotionPage], title: str) -> Optional[NotionPage]:
    """Find Notion page by title.
    
    Args:
        pages: List of Notion pages
        title: Title to search for
        
    Returns:
        NotionPage or None
    """
    title_lower = title.lower().strip()
    
    for page in pages:
        page_title = page.get_title().lower().strip()
        if page_title == title_lower:
            return page
    
    return None


def main():
    """Main update function."""
    console.print(Panel.fit(
        "[bold]Update Jira Tasks from Notion[/bold]\n"
        "[dim]Updating existing tasks with full content...[/dim]",
        border_style="blue"
    ))
    
    # Check configuration
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")
    
    if not all([jira_url, jira_email, jira_token, project_key]):
        console.print("[red]Error: Jira credentials not configured in .env[/red]")
        return 1
    
    # Dry run mode
    console.print("\n[bold yellow]Update mode:[/bold yellow]")
    console.print("1. [cyan]DRY RUN[/cyan] - Preview what will be updated")
    console.print("2. [green]REAL MODE[/green] - Actually update tasks\n")
    
    dry_run = True  # Change to False for real updates
    
    if dry_run:
        console.print("[bold yellow]DRY RUN MODE - No tasks will be updated[/bold yellow]\n")
    else:
        console.print("[bold green]REAL UPDATE MODE - Updating tasks![/bold green]\n")
    
    try:
        # Load Notion data from local storage
        console.print("[blue]Loading Notion data from local storage...[/blue]")
        storage = NotionStorage()
        pages = storage.load_all_pages()
        console.print(f"[green]Loaded {len(pages)} pages from storage[/green]\n")
        
        # Connect to Jira
        console.print("[blue]Connecting to Jira...[/blue]")
        jira_client = JiraClient(jira_url, jira_email, jira_token)
        console.print(f"[green]Connected to Jira project: {project_key}[/green]\n")
        
        # Search for tasks with notion-import label
        console.print("[blue]Searching for Notion-imported tasks in Jira...[/blue]")
        jql = f'project = {project_key} AND labels = "notion-import"'
        issues = jira_client.search_issues(jql, max_results=100)
        
        console.print(f"[green]Found {len(issues)} tasks to update[/green]\n")
        
        if not issues:
            console.print("[yellow]No tasks found with 'notion-import' label[/yellow]")
            return 0
        
        # Show preview
        console.print("[bold blue]Tasks to update:[/bold blue]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Jira Key", style="cyan", width=10)
        table.add_column("Title", width=50)
        table.add_column("Found in Notion", style="green", width=15)
        
        matches = []
        
        for issue in issues[:10]:
            key = issue['key']
            title = issue['fields']['summary']
            
            # Find matching Notion page
            notion_page = find_notion_page_by_title(pages, title)
            
            if notion_page:
                matches.append((key, title, notion_page))
                table.add_row(key, title[:50], "✓ Yes")
            else:
                table.add_row(key, title[:50], "✗ No")
        
        if len(issues) > 10:
            table.add_row("...", f"... and {len(issues) - 10} more", "")
        
        console.print(table)
        
        console.print(f"\n[cyan]Found {len(matches)} matching tasks (showing first 10)[/cyan]\n")
        
        # Update tasks
        console.print("[bold blue]Updating tasks...[/bold blue]\n")
        
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task_progress = progress.add_task(
                f"[cyan]Processing {len(issues)} tasks...",
                total=len(issues)
            )
            
            for issue in issues:
                key = issue['key']
                title = issue['fields']['summary']
                
                # Find matching Notion page
                notion_page = find_notion_page_by_title(pages, title)
                
                if not notion_page:
                    skipped_count += 1
                    progress.advance(task_progress)
                    continue
                
                try:
                    if dry_run:
                        console.print(f"[dim]Would update {key}: {title[:50]}...[/dim]")
                        console.print(f"[dim]  - Blocks: {len(notion_page.blocks)}[/dim]")
                        console.print(f"[dim]  - Todos: {len(notion_page.get_todo_items())}[/dim]")
                        updated_count += 1
                    else:
                        # Build rich description
                        description_adf = build_rich_description_adf(notion_page)
                        
                        # Update labels
                        labels = issue['fields'].get('labels', [])
                        if 'full-content' not in labels:
                            labels.append('full-content')
                        if notion_page.get_todo_items() and 'has-checklist' not in labels:
                            labels.append('has-checklist')
                        if notion_page.get_images() and 'has-images' not in labels:
                            labels.append('has-images')
                        if notion_page.get_files() and 'has-files' not in labels:
                            labels.append('has-files')
                        
                        # Update issue
                        update_data = {
                            "fields": {
                                "description": description_adf,
                                "labels": labels
                            }
                        }
                        
                        jira_client.update_issue(key, update_data)
                        console.print(f"[green]Updated {key}: {title[:50]}[/green]")
                        updated_count += 1
                        
                except Exception as e:
                    console.print(f"[red]Error updating {key}: {e}[/red]")
                    failed_count += 1
                
                progress.advance(task_progress)
        
        # Summary
        console.print("\n[bold blue]Update Summary[/bold blue]\n")
        
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green", justify="right")
        
        stats_table.add_row("Total tasks found", str(len(issues)))
        stats_table.add_row("Successfully updated", str(updated_count))
        stats_table.add_row("Skipped (no match)", str(skipped_count))
        stats_table.add_row("Failed", str(failed_count))
        
        console.print(stats_table)
        
        if dry_run:
            console.print("\n[yellow]DRY RUN: No tasks were actually updated[/yellow]")
            console.print("\n[bold]To actually update tasks:[/bold]")
            console.print("1. Set dry_run=False in the script")
            console.print("2. Run the script again")
        else:
            console.print(f"\n[bold green]Updated {updated_count} tasks![/bold green]")
            if updated_count > 0:
                console.print(f"\nCheck tasks in Jira: {jira_url}/browse/{project_key}")
        
        jira_client.close()
        
        console.print("\n[bold green]Update completed![/bold green]")
        return 0
        
    except Exception as e:
        console.print(f"\n[red]Update failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())







