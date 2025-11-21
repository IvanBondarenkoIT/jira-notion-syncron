"""Get Jira boards and their IDs.

This script helps you get Board IDs for departments configuration.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    import requests
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv requests rich --quiet")
    from dotenv import load_dotenv
    import requests
    from rich.console import Console
    from rich.table import Table

load_dotenv()
console = Console()

def get_jira_boards():
    """Get all boards from Jira."""
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, jira_email, jira_token]):
        console.print("[red]Error: Jira credentials not configured[/red]")
        return
    
    console.print("[blue]Fetching boards from Jira...[/blue]\n")
    
    try:
        # Get all boards
        url = f"{jira_url}/rest/agile/1.0/board"
        params = {"maxResults": 50}
        
        response = requests.get(
            url,
            auth=(jira_email, jira_token),
            headers={"Accept": "application/json"},
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/red]")
            console.print(response.text[:500])
            return
        
        data = response.json()
        boards = data.get("values", [])
        
        if not boards:
            console.print("[yellow]No boards found[/yellow]")
            return
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Board ID", style="cyan", width=10)
        table.add_column("Name", style="green", width=40)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Location", width=30)
        
        for board in boards:
            board_id = str(board.get("id", "N/A"))
            name = board.get("name", "Unknown")
            board_type = board.get("type", "N/A")
            location = board.get("location", {}).get("displayName", "N/A")
            
            table.add_row(board_id, name, board_type, location)
        
        console.print(table)
        console.print(f"\n[green]Found {len(boards)} boards[/green]")
        console.print("\n[yellow]Copy Board IDs to config/departments.yaml[/yellow]\n")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    get_jira_boards()


