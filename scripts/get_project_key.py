"""Get correct Jira project key.

This script helps find the correct project key for .env file.
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

def get_projects():
    """Get all projects."""
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, jira_email, jira_token]):
        console.print("[red]Error: Jira credentials not configured[/red]")
        return
    
    console.print("[blue]Fetching projects from Jira...[/blue]\n")
    
    try:
        url = f"{jira_url}/rest/api/3/project"
        
        response = requests.get(
            url,
            auth=(jira_email, jira_token),
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/red]")
            console.print(response.text[:500])
            return
        
        projects = response.json()
        
        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Project Key", style="cyan", width=15)
        table.add_column("Name", style="green", width=40)
        table.add_column("Type", width=15)
        
        for project in projects:
            key = project.get("key", "N/A")
            name = project.get("name", "Unknown")
            project_type = project.get("projectTypeKey", "N/A")
            
            table.add_row(key, name, project_type)
        
        console.print(table)
        console.print(f"\n[green]Found {len(projects)} projects[/green]")
        console.print("\n[yellow]Copy the Project Key (e.g., 'KAN') to .env as JIRA_PROJECT_KEY[/yellow]\n")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    get_projects()



