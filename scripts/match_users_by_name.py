"""Match users by display name and update users.json.

Since users might have different emails in Jira,
we'll search by display name.
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
    from rich.prompt import Prompt
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv requests rich --quiet")
    from dotenv import load_dotenv
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Prompt

load_dotenv()
console = Console()


def get_all_jira_users():
    """Get all users from Jira."""
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    try:
        url = f"{jira_url}/rest/api/3/users/search"
        params = {"maxResults": 100}
        
        response = requests.get(
            url,
            auth=(jira_email, jira_token),
            headers={"Accept": "application/json"},
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return []
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return []


def main():
    """Match users by name."""
    console.print("[bold blue]Matching Users by Name[/bold blue]\n")
    
    # Get all Jira users
    jira_users = get_all_jira_users()
    
    if not jira_users:
        console.print("[red]No users found in Jira[/red]")
        return
    
    # Show all Jira users
    console.print(f"[green]Found {len(jira_users)} users in Jira[/green]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=5)
    table.add_column("Display Name", style="green", width=30)
    table.add_column("Email", width=35)
    table.add_column("Account ID", width=25)
    
    for idx, user in enumerate(jira_users, 1):
        if user.get("active", False):
            display_name = user.get("displayName", "Unknown")
            email = user.get("emailAddress", "N/A")
            account_id = user.get("accountId", "N/A")
            
            table.add_row(
                str(idx),
                display_name,
                email[:35] if email != "N/A" else "N/A",
                account_id[:25] + "..." if len(account_id) > 25 else account_id
            )
    
    console.print(table)
    
    # Load our users
    users_file = project_root / "data" / "users" / "users.json"
    with open(users_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    our_users = data.get("users", [])
    
    console.print("\n[bold blue]Our Users (need to match):[/bold blue]\n")
    
    # Names to match
    names_to_match = {
        "Саша": ["Саша", "Sasha", "Alexander", "Alex", "Александр"],
        "Настя": ["Настя", "Nastya", "Anastasia", "Анастасия"],
        "Иван": ["Иван", "Ivan"],
        "Александр": ["Александр", "Alexander", "Alex"],
        "DimKava": ["DimKava", "DimKava"]
    }
    
    # Try to auto-match
    updated = False
    
    for user in our_users:
        if user.get("jira_account_id"):
            console.print(f"[green]{user['name']}: Already has Account ID[/green]")
            continue
        
        user_name = user.get("name", "")
        possible_names = names_to_match.get(user_name, [user_name])
        
        # Try to find match
        for jira_user in jira_users:
            if not jira_user.get("active"):
                continue
                
            display_name = jira_user.get("displayName", "")
            
            # Check if any possible name matches
            for possible_name in possible_names:
                if possible_name.lower() in display_name.lower():
                    account_id = jira_user.get("accountId")
                    
                    console.print(f"\n[yellow]Match found for {user_name}:[/yellow]")
                    console.print(f"  Jira user: {display_name}")
                    console.print(f"  Email: {jira_user.get('emailAddress', 'N/A')}")
                    console.print(f"  Account ID: {account_id}")
                    
                    confirm = Prompt.ask(
                        f"  Use this match for {user_name}?",
                        choices=["y", "n"],
                        default="y"
                    )
                    
                    if confirm == "y":
                        user["jira_account_id"] = account_id
                        updated = True
                        console.print(f"[green]  Updated {user_name}![/green]")
                    
                    break
            
            if user.get("jira_account_id"):
                break
        
        # If still not matched, ask manually
        if not user.get("jira_account_id"):
            console.print(f"\n[yellow]No automatic match for {user_name}[/yellow]")
            console.print(f"Email we have: {user.get('email')}")
            
            console.print("\nLook at the table above and enter:")
            choice = Prompt.ask(
                f"  Number of Jira user for {user_name} (or 's' to skip)",
                default="s"
            )
            
            if choice != "s" and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(jira_users):
                    jira_user = jira_users[idx]
                    user["jira_account_id"] = jira_user.get("accountId")
                    updated = True
                    console.print(f"[green]  Updated {user_name}![/green]")
    
    # Save if updated
    if updated:
        data["users"] = our_users
        data["metadata"]["last_updated"] = "2024-10-28"
        
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        console.print("\n[green][OK] Updated users.json with Account IDs[/green]\n")
        
        # Show summary
        console.print("[bold blue]Summary:[/bold blue]\n")
        for user in our_users:
            name = user.get("name")
            account_id = user.get("jira_account_id", "NOT SET")
            if account_id and account_id != "NOT SET":
                console.print(f"[green]  {name}: {account_id[:25]}...[/green]")
            else:
                console.print(f"[yellow]  {name}: NOT SET[/yellow]")
    else:
        console.print("\n[yellow]No updates made[/yellow]")


if __name__ == "__main__":
    main()



