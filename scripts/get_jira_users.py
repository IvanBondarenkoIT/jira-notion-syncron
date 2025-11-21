"""Get Jira users and their Account IDs.

This script helps you get Account IDs for your users from Jira.
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

def get_jira_users():
    """Get all users from Jira."""
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, jira_email, jira_token]):
        console.print("[red]Error: Jira credentials not configured[/red]")
        return
    
    console.print("[blue]Fetching users from Jira...[/blue]\n")
    
    try:
        # Get all users (limit 100)
        url = f"{jira_url}/rest/api/3/users/search"
        params = {"maxResults": 100}
        
        response = requests.get(
            url,
            auth=(jira_email, jira_token),
            headers={"Accept": "application/json"},
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            console.print(f"[red]Error: {response.status_code}[/red]")
            console.print(response.text)
            return
        
        users = response.json()
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Display Name", style="cyan", width=25)
        table.add_column("Email", style="green", width=30)
        table.add_column("Account ID", style="yellow", width=40)
        
        for user in users:
            display_name = user.get("displayName", "Unknown")
            email = user.get("emailAddress", "N/A")
            account_id = user.get("accountId", "N/A")
            
            # Only show active users
            if user.get("active", False):
                table.add_row(display_name, email, account_id)
        
        console.print(table)
        console.print(f"\n[green]Found {len(users)} users[/green]")
        console.print("\n[yellow]Copy Account IDs to data/users/users.json[/yellow]\n")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    get_jira_users()


