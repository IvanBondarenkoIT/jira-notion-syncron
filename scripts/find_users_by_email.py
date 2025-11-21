"""Find Jira users by email and update users.json with Account IDs.

This script:
1. Reads users from data/users/users.json
2. Searches for them in Jira by email
3. Updates the file with Jira Account IDs
"""

import json
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
    from rich.panel import Panel
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv requests rich --quiet")
    from dotenv import load_dotenv
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

load_dotenv()
console = Console()


def load_users():
    """Load users from users.json."""
    users_file = project_root / "data" / "users" / "users.json"
    
    if not users_file.exists():
        console.print("[red]Error: data/users/users.json not found[/red]")
        return None
    
    with open(users_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("users", [])


def find_user_by_email(email, jira_url, jira_email, jira_token):
    """Find user in Jira by email."""
    try:
        # Search for user by email
        url = f"{jira_url}/rest/api/3/user/search"
        params = {"query": email}
        
        response = requests.get(
            url,
            auth=(jira_email, jira_token),
            headers={"Accept": "application/json"},
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            return None, f"Error {response.status_code}"
        
        users = response.json()
        
        # Find exact match by email
        for user in users:
            if user.get("emailAddress", "").lower() == email.lower():
                return user.get("accountId"), user.get("displayName", "Unknown")
        
        return None, "Not found"
        
    except Exception as e:
        return None, f"Error: {str(e)}"


def main():
    """Main function."""
    console.print(Panel.fit(
        "[bold]Find Jira Users by Email[/bold]\n"
        "[dim]Searching for users in Jira...[/dim]",
        border_style="blue"
    ))
    
    # Load configuration
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, jira_email, jira_token]):
        console.print("[red]Error: Jira credentials not configured in .env[/red]")
        return
    
    # Load users
    users = load_users()
    if not users:
        return
    
    console.print(f"\n[blue]Loaded {len(users)} users from users.json[/blue]\n")
    
    # Search for each user
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Email", style="green", width=30)
    table.add_column("Status", width=15)
    table.add_column("Jira Account ID", width=30)
    
    found_count = 0
    
    for user in users:
        name = user.get("name", "Unknown")
        email = user.get("email", "")
        current_account_id = user.get("jira_account_id", "")
        
        if current_account_id:
            # Already has account ID
            table.add_row(
                name,
                email,
                "[green]Already set[/green]",
                current_account_id[:20] + "..."
            )
            found_count += 1
            continue
        
        # Search in Jira
        console.print(f"[dim]Searching for {email}...[/dim]")
        account_id, status = find_user_by_email(email, jira_url, jira_email, jira_token)
        
        if account_id:
            user["jira_account_id"] = account_id
            table.add_row(
                name,
                email,
                "[green]FOUND[/green]",
                account_id[:20] + "..."
            )
            found_count += 1
        else:
            table.add_row(
                name,
                email,
                "[yellow]NOT FOUND[/yellow]",
                status
            )
    
    console.print(table)
    console.print(f"\n[bold]Found: {found_count}/{len(users)} users in Jira[/bold]\n")
    
    # Save updated users.json
    if found_count > 0:
        users_file = project_root / "data" / "users" / "users.json"
        
        with open(users_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        data["users"] = users
        data["metadata"]["last_updated"] = "2024-10-28"
        
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        console.print("[green][OK] Updated users.json with Jira Account IDs[/green]\n")
    
    # Show users not found
    not_found = [u for u in users if not u.get("jira_account_id")]
    if not_found:
        console.print("[yellow]Users not found in Jira:[/yellow]")
        for user in not_found:
            console.print(f"  - {user['name']} ({user['email']})")
        
        console.print("\n[bold blue]To add users to Jira:[/bold blue]")
        console.print("1. Go to: https://your-domain.atlassian.net/admin/users")
        console.print("2. Click 'Invite users'")
        console.print("3. Enter their email addresses")
        console.print("4. Run this script again to get their Account IDs\n")


if __name__ == "__main__":
    main()



