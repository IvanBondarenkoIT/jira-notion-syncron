"""Main CLI entry point."""

import sys
from pathlib import Path

import click
from loguru import logger
from rich.console import Console
from rich.table import Table

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Jira-Notion Synchronization CLI.
    
    Enterprise-grade система для синхронизации задач из различных источников.
    """
    logger.add("logs/app.log", rotation="1 day", retention="7 days", level="INFO")


@cli.command()
@click.option("--dry-run", is_flag=True, help="Run without making actual changes")
@click.option("--continuous", is_flag=True, help="Run continuously")
def sync(dry_run: bool, continuous: bool) -> None:
    """Start synchronization process.
    
    Args:
        dry_run: If True, no actual changes will be made
        continuous: If True, run continuously
    """
    console.print("[bold blue]Starting synchronization...[/bold blue]")
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
    
    try:
        # TODO: Implement actual sync logic
        console.print("[green]Synchronization completed successfully[/green]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        logger.exception("Synchronization failed")
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--format", type=click.Choice(["csv", "excel", "text"]), help="File format")
def import_data(file_path: str, format: str | None) -> None:
    """Import data from file.
    
    Args:
        file_path: Path to the file to import
        format: File format (auto-detected if not specified)
    """
    console.print(f"[bold blue]Importing data from {file_path}...[/bold blue]")
    
    try:
        # TODO: Implement import logic
        console.print("[green]Data imported successfully[/green]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        logger.exception("Import failed")
        sys.exit(1)


@cli.command()
def stats() -> None:
    """Display statistics."""
    console.print("[bold blue]Statistics[/bold blue]\n")
    
    # Create a table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")
    
    # TODO: Get actual statistics
    table.add_row("Total Tasks", "0")
    table.add_row("Active Sprints", "0")
    table.add_row("Departments", "3")
    table.add_row("Users", "4")
    
    console.print(table)


@cli.command()
def config() -> None:
    """Display configuration."""
    console.print("[bold blue]Configuration[/bold blue]\n")
    
    # TODO: Load and display actual config
    console.print("[yellow]Configuration will be displayed here[/yellow]")


@cli.command()
@click.option("--department", help="Filter by department")
def users(department: str | None) -> None:
    """List users.
    
    Args:
        department: Filter by department
    """
    console.print("[bold blue]Users[/bold blue]\n")
    
    # Create a table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Department", style="yellow")
    table.add_column("Role", style="green")
    
    # TODO: Load and display actual users
    table.add_row("user_001", "Саша", "marketing", "marketing_specialist")
    table.add_row("user_002", "Настя", "marketing", "marketing_specialist")
    table.add_row("user_003", "Иван", "hr", "hr_specialist")
    table.add_row("user_004", "Директор", "management", "director")
    
    console.print(table)


if __name__ == "__main__":
    cli()

