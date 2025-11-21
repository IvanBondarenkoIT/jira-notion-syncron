"""Migrate tasks from Notion to Jira with FULL content extraction.

This script:
1. Extracts complete page content from Notion (blocks, todos, images, files)
2. Saves full data to local storage
3. Creates rich descriptions in Jira with all content
4. Maps users and shows progress
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

from src.infrastructure.notion.notion_client import NotionClient
from src.infrastructure.notion.notion_storage import NotionStorage
from src.infrastructure.jira.jira_client import JiraClient
from src.infrastructure.jira.jira_repository import JiraTaskRepository
from src.domain.models.task import Priority, TaskType
from src.domain.models.notion_block import NotionPage
from src.application.use_cases.create_task_in_jira import CreateTaskInJiraUseCase

load_dotenv()
console = Console()

# Default assignee (DimKava)
DEFAULT_ASSIGNEE_ID = "712020:3bcced1b-9ddd-488d-b6fd-e0e8fc0e97a3"

# User mapping (Notion name -> Jira Account ID)
USER_MAPPING = {
    "Ivan": "712020:c40dface-b447-489f-865f-bf7b9ac9db3b",
    "Sasha SW": DEFAULT_ASSIGNEE_ID,
    "Sasha": DEFAULT_ASSIGNEE_ID,
    "Anastasiia": "5ee270d1f557470aba0bb722",
    "Nastya": "5ee270d1f557470aba0bb722",
    "Nini": DEFAULT_ASSIGNEE_ID,
    "alex fedorov": "61e6b99b78cb6900714753ae",
    "Elana Fedorova": DEFAULT_ASSIGNEE_ID,
    "DimKava": DEFAULT_ASSIGNEE_ID,
}


def build_rich_description(page: NotionPage) -> str:
    """Build rich Jira description from Notion page.
    
    Args:
        page: NotionPage with full content
        
    Returns:
        Rich description text
    """
    parts = []
    
    # Content
    content = page.get_content_markdown()
    if content and content.strip():
        parts.append("h2. Описание задачи\n")
        parts.append(content)
        parts.append("\n")
    
    # Todo items
    todos = page.get_todo_items()
    if todos:
        parts.append("h2. Чеклист\n")
        for todo in todos:
            checkbox = "(/) " if todo.checked else "(x) "
            parts.append(f"{checkbox}{todo.get_plain_text()}\n")
        parts.append("\n")
    
    # Images
    images = page.get_images()
    if images:
        parts.append("h2. Изображения\n")
        for img in images:
            if img.file:
                caption = img.get_caption_text() or "Image"
                parts.append(f"!{img.file.url}|thumbnail!\n")
                if caption and caption != "Image":
                    parts.append(f"_{caption}_\n")
        parts.append("\n")
    
    # Files
    files = page.get_files()
    if files:
        parts.append("h2. Файлы\n")
        for file in files:
            if file.file:
                name = file.file.name or "File"
                parts.append(f"[{name}|{file.file.url}]\n")
        parts.append("\n")
    
    # Links
    links = page.get_links()
    if links:
        unique_links = list(set(links))
        if unique_links:
            parts.append("h2. Ссылки\n")
            for link in unique_links:
                parts.append(f"[{link}|{link}]\n")
            parts.append("\n")
    
    # Metadata
    parts.append("----\n")
    parts.append("h3. Метаданные\n")
    
    # Get properties
    status = page.get_property_value("Status")
    priority = page.get_property_value("Priority")
    effort = page.get_property_value("Effort level")
    due_date = page.get_property_value("Due date")
    tags = page.get_property_value("Task type")
    
    if status:
        parts.append(f"*Статус в Notion:* {status}\n")
    if priority:
        parts.append(f"*Приоритет:* {priority}\n")
    if effort:
        parts.append(f"*Уровень усилий:* {effort}\n")
    if due_date:
        parts.append(f"*Срок:* {due_date}\n")
    if tags:
        if isinstance(tags, list):
            parts.append(f"*Теги:* {', '.join(tags)}\n")
        else:
            parts.append(f"*Теги:* {tags}\n")
    
    parts.append(f"\n*Оригинал в Notion:* [{page.url}|{page.url}]\n")
    parts.append(f"*Импортировано:* {page.created_time.strftime('%Y-%m-%d')}\n")
    
    return "".join(parts)


def map_priority(notion_priority: Optional[str]) -> Priority:
    """Map Notion priority to Jira priority."""
    if not notion_priority:
        return Priority.MEDIUM
    
    priority_lower = notion_priority.lower()
    
    if any(word in priority_lower for word in ["critical", "urgent", "критичный", "срочный"]):
        return Priority.CRITICAL
    elif any(word in priority_lower for word in ["high", "важный", "высокий"]):
        return Priority.HIGH
    elif any(word in priority_lower for word in ["low", "низкий"]):
        return Priority.LOW
    else:
        return Priority.MEDIUM


def get_jira_account_id(assignee_names: Optional[List[str]]) -> str:
    """Get Jira Account ID for assignee."""
    if not assignee_names:
        return DEFAULT_ASSIGNEE_ID
    
    # Try first assignee
    assignee_name = assignee_names[0] if isinstance(assignee_names, list) else str(assignee_names)
    
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


def create_jira_task(
    page: NotionPage,
    use_case: CreateTaskInJiraUseCase,
    dry_run: bool = True
) -> Optional[str]:
    """Create task in Jira from Notion page.
    
    Args:
        page: NotionPage with full content
        use_case: Jira use case
        dry_run: If True, don't actually create
        
    Returns:
        Jira issue key or None
    """
    try:
        # Get title and clean it (Jira doesn't allow newlines in summary)
        title = page.get_title()
        title = " ".join(title.split())  # Replace all whitespace (including newlines) with single spaces
        title = title[:255]  # Jira has a max summary length
        
        # Build rich description
        description = build_rich_description(page)
        
        # Get assignee - temporarily disable to test
        # assignee_names = page.get_property_value("Assignee") or []
        # # Handle people property - it returns list of dicts with names
        # if assignee_names and isinstance(assignee_names, list):
        #     if isinstance(assignee_names[0], dict):
        #         assignee_names = [p.get("name", "") for p in assignee_names]
        
        # assignee_id = get_jira_account_id(assignee_names)
        assignee_id = None  # Temporarily disable assignee
        
        # Map priority
        priority_value = page.get_property_value("Priority")
        priority = map_priority(priority_value)
        
        # Labels
        labels = ["notion-import", "full-content"]
        
        tags = page.get_property_value("Task type")
        if tags:
            if isinstance(tags, list):
                labels.extend([tag.lower().replace(" ", "-") for tag in tags if tag])
            else:
                labels.append(str(tags).lower().replace(" ", "-"))
        
        # Add metadata labels
        if page.get_todo_items():
            labels.append("has-checklist")
        if page.get_images():
            labels.append("has-images")
        if page.get_files():
            labels.append("has-files")
        
        if dry_run:
            console.print(f"[dim]Would create: {title}[/dim]")
            console.print(f"[dim]  - Blocks: {len(page.blocks)}[/dim]")
            console.print(f"[dim]  - Todos: {len(page.get_todo_items())}[/dim]")
            console.print(f"[dim]  - Images: {len(page.get_images())}[/dim]")
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
        console.print(f"[red]Error creating task '{page.get_title()}': {e}[/red]")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main migration function."""
    console.print(Panel.fit(
        "[bold]Notion to Jira Migration (FULL CONTENT)[/bold]\n"
        "[dim]Extracting complete content: blocks, todos, images, files...[/dim]",
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
        return 1
    
    if not all([jira_url, jira_email, jira_token, project_key]):
        console.print("[red]Error: Jira credentials not configured in .env[/red]")
        return 1
    
    # Mode selection
    console.print("\n[bold yellow]Migration mode:[/bold yellow]")
    console.print("1. [cyan]DRY RUN[/cyan] - Preview what will be created")
    console.print("2. [green]REAL MODE[/green] - Actually create tasks in Jira\n")
    
    dry_run = False  # Change to True for dry-run mode
    
    if dry_run:
        console.print("[bold yellow]DRY RUN MODE - No tasks will be created[/bold yellow]\n")
    else:
        console.print("[bold green]REAL MIGRATION MODE - Creating tasks![/bold green]\n")
    
    try:
        # Initialize Notion client
        console.print("[blue]Connecting to Notion...[/blue]")
        notion_client = NotionClient(notion_token)
        storage = NotionStorage()
        
        # Fetch pages with full content
        console.print("[blue]Fetching pages with full content...[/blue]")
        console.print("[dim]This includes: blocks, todos, images, files, links...[/dim]\n")
        
        pages = notion_client.get_database_pages(notion_db_id, include_content=True)
        
        if not pages:
            console.print("[yellow]No pages found in Notion database[/yellow]")
            return 0
        
        console.print(f"[green]Fetched {len(pages)} pages with full content[/green]\n")
        
        # Save to local storage
        console.print("[blue]Saving full content to local storage...[/blue]")
        storage.save_pages(pages, save_markdown=True)
        console.print(f"[green]Saved to {storage.storage_dir}[/green]\n")
        
        # Show preview
        console.print("[bold blue]Pages to migrate:[/bold blue]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=5)
        table.add_column("Title", width=35)
        table.add_column("Assignee", style="green", width=12)
        table.add_column("Blocks", style="yellow", width=7)
        table.add_column("Todos", style="blue", width=7)
        table.add_column("Images", style="magenta", width=7)
        
        for idx, page in enumerate(pages[:10], 1):
            assignee_names = page.get_property_value("Assignee") or []
            if assignee_names and isinstance(assignee_names, list):
                assignee = assignee_names[0] if assignee_names else "DimKava"
            else:
                assignee = "DimKava"
            
            table.add_row(
                str(idx),
                page.get_title()[:35],
                str(assignee)[:12],
                str(len(page.blocks)),
                str(len(page.get_todo_items())),
                str(len(page.get_images()))
            )
        
        if len(pages) > 10:
            table.add_row("...", f"... and {len(pages) - 10} more", "", "", "", "")
        
        console.print(table)
        
        # Initialize Jira
        if not dry_run:
            console.print(f"\n[blue]Connecting to Jira...[/blue]")
            jira_client = JiraClient(jira_url, jira_email, jira_token)
            jira_repository = JiraTaskRepository(jira_client, project_key)
            use_case = CreateTaskInJiraUseCase(jira_repository)
            console.print(f"[green]Connected to Jira project: {project_key}[/green]\n")
        else:
            use_case = None
        
        # Migrate tasks
        console.print("[bold blue]Starting migration...[/bold blue]\n")
        
        created_keys = []
        failed_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task_progress = progress.add_task(
                f"[cyan]Processing {len(pages)} pages...",
                total=len(pages)
            )
            
            for page in pages:
                if not dry_run:
                    result = create_jira_task(page, use_case, dry_run=False)
                    if result:
                        created_keys.append(result)
                    else:
                        failed_count += 1
                else:
                    create_jira_task(page, use_case, dry_run=True)
                
                progress.advance(task_progress)
        
        # Summary
        console.print("\n[bold blue]Migration Summary[/bold blue]\n")
        
        # Statistics
        stats = storage.export_statistics()
        
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green", justify="right")
        
        stats_table.add_row("Total pages", str(stats["total_pages"]))
        stats_table.add_row("Total blocks extracted", str(stats["total_blocks"]))
        stats_table.add_row("Total todo items", str(stats["total_todos"]))
        stats_table.add_row("Total images", str(stats["total_images"]))
        stats_table.add_row("Total files", str(stats["total_files"]))
        stats_table.add_row("Total links", str(stats["total_links"]))
        
        console.print(stats_table)
        
        if dry_run:
            console.print("\n[yellow]DRY RUN: No tasks were created[/yellow]")
            console.print("\n[bold]To actually create tasks:[/bold]")
            console.print("1. Set dry_run=False in the script")
            console.print("2. Run the script again")
        else:
            console.print(f"\n[green]Successfully created: {len(created_keys)} tasks[/green]")
            console.print(f"[red]Failed: {failed_count} tasks[/red]")
            
            if created_keys:
                console.print("\n[bold]Created issues:[/bold]")
                for key in created_keys[:10]:
                    console.print(f"  - {jira_url}/browse/{key}")
                
                if len(created_keys) > 10:
                    console.print(f"  ... and {len(created_keys) - 10} more")
        
        console.print(f"\n[bold]Local storage:[/bold]")
        console.print(f"  JSON: {storage.pages_dir}")
        console.print(f"  Markdown: {storage.markdown_dir}")
        
        notion_client.close()
        if not dry_run:
            jira_client.close()
        
        console.print("\n[bold green]Migration completed![/bold green]")
        return 0
        
    except Exception as e:
        console.print(f"\n[red]Migration failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

