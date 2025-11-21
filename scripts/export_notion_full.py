"""Export complete Notion database with full content.

This script:
1. Connects to Notion API
2. Fetches all pages from database
3. Extracts complete page content (blocks, todo-lists, images, files)
4. Saves to local storage (JSON + Markdown)
5. Shows statistics
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv rich --quiet")
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.infrastructure.notion.notion_client import NotionClient
from src.infrastructure.notion.notion_storage import NotionStorage

load_dotenv()
console = Console()


def main():
    """Main export function."""
    console.print(Panel.fit(
        "[bold]Notion Full Export[/bold]\n"
        "[dim]Extracting complete page content with blocks, todos, images, files...[/dim]",
        border_style="blue"
    ))
    
    # Check configuration
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db_id = os.getenv("NOTION_DATABASE_ID")
    
    if not all([notion_token, notion_db_id]):
        console.print("[red]Error: Notion credentials not configured in .env[/red]")
        console.print("[yellow]Add NOTION_TOKEN and NOTION_DATABASE_ID to .env[/yellow]")
        return 1
    
    # Initialize services
    console.print("\n[blue]Initializing Notion client...[/blue]")
    
    try:
        client = NotionClient(notion_token)
        storage = NotionStorage()
        
        console.print(f"[green]Storage directory: {storage.storage_dir}[/green]\n")
        
        # Fetch pages with content
        console.print("[bold blue]Fetching pages from Notion...[/bold blue]")
        console.print("[dim]This may take a while for large databases...[/dim]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            fetch_task = progress.add_task(
                "[cyan]Fetching pages...",
                total=None
            )
            
            pages = client.get_database_pages(
                notion_db_id,
                include_content=True
            )
            
            progress.update(fetch_task, completed=True)
        
        if not pages:
            console.print("[yellow]No pages found in database[/yellow]")
            return 0
        
        console.print(f"[green]Fetched {len(pages)} pages[/green]\n")
        
        # Show preview
        console.print("[bold blue]Pages preview:[/bold blue]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=5)
        table.add_column("Title", width=40)
        table.add_column("Blocks", style="yellow", width=8)
        table.add_column("Todos", style="green", width=8)
        table.add_column("Images", style="blue", width=8)
        table.add_column("Files", style="red", width=8)
        
        for idx, page in enumerate(pages[:10], 1):
            table.add_row(
                str(idx),
                page.get_title()[:40],
                str(len(page.blocks)),
                str(len(page.get_todo_items())),
                str(len(page.get_images())),
                str(len(page.get_files()))
            )
        
        if len(pages) > 10:
            table.add_row("...", f"... and {len(pages) - 10} more", "", "", "", "")
        
        console.print(table)
        
        # Save to storage
        console.print(f"\n[bold blue]Saving to local storage...[/bold blue]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            save_task = progress.add_task(
                f"[cyan]Saving {len(pages)} pages...",
                total=len(pages)
            )
            
            saved_paths = storage.save_pages(pages, save_markdown=True)
            
            progress.update(save_task, completed=len(pages))
        
        console.print(f"[green]Saved {len(saved_paths)} pages[/green]")
        
        # Show statistics
        console.print("\n[bold blue]Export Statistics[/bold blue]\n")
        
        stats = storage.export_statistics()
        
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green", justify="right")
        
        stats_table.add_row("Total pages", str(stats["total_pages"]))
        stats_table.add_row("Total blocks", str(stats["total_blocks"]))
        stats_table.add_row("Pages with todos", str(stats["pages_with_todos"]))
        stats_table.add_row("Pages with images", str(stats["pages_with_images"]))
        stats_table.add_row("Pages with files", str(stats["pages_with_files"]))
        stats_table.add_row("Total todo items", str(stats["total_todos"]))
        stats_table.add_row("Total images", str(stats["total_images"]))
        stats_table.add_row("Total files", str(stats["total_files"]))
        stats_table.add_row("Total links", str(stats["total_links"]))
        
        console.print(stats_table)
        
        # Show file locations
        console.print(f"\n[bold]Files saved to:[/bold]")
        console.print(f"  JSON: {storage.pages_dir}")
        console.print(f"  Markdown: {storage.markdown_dir}")
        console.print(f"  Index: {storage.index_file}")
        
        # Example: Show one page with todos
        pages_with_todos = [p for p in pages if p.get_todo_items()]
        if pages_with_todos:
            example_page = pages_with_todos[0]
            console.print(f"\n[bold blue]Example: '{example_page.get_title()}'[/bold blue]")
            console.print(f"[dim]Todo items:[/dim]\n")
            
            for todo in example_page.get_todo_items()[:5]:
                checkbox = "[x]" if todo.checked else "[ ]"
                console.print(f"  {checkbox} {todo.get_plain_text()}")
            
            if len(example_page.get_todo_items()) > 5:
                console.print(f"  ... and {len(example_page.get_todo_items()) - 5} more")
        
        client.close()
        
        console.print("\n[bold green]Export completed successfully![/bold green]")
        return 0
        
    except Exception as e:
        console.print(f"\n[red]Export failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())







