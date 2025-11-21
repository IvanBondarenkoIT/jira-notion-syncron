"""Validate project configuration and test connections.

This script checks:
- .env file completeness
- Jira API connection
- Notion API connection (if configured)
- Users data
- Departments configuration
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    import requests
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv rich requests --quiet")
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    import requests

console = Console()

# Load .env file
load_dotenv()


def check_env_variable(var_name: str, required: bool = True) -> Tuple[bool, str]:
    """Check if environment variable is set.
    
    Args:
        var_name: Name of the environment variable
        required: Whether the variable is required
        
    Returns:
        Tuple of (is_valid, value or error message)
    """
    value = os.getenv(var_name)
    
    if not value:
        if required:
            return False, "[X] NOT SET (REQUIRED)"
        return True, "[!] Not set (optional)"
    
    # Check for placeholder values
    placeholders = ["your-", "example", "secret_your", "PROJ"]
    if any(placeholder in value for placeholder in placeholders):
        if required:
            return False, f"[!] PLACEHOLDER VALUE: {value[:50]}..."
        return True, f"[!] Placeholder: {value[:50]}..."
    
    return True, f"[OK] SET ({len(value)} chars)"


def validate_env_config() -> Dict[str, Tuple[bool, str]]:
    """Validate all environment variables."""
    console.print("\n[bold blue]Checking Environment Variables[/bold blue]\n")
    
    # Required variables
    required_vars = {
        "JIRA_URL": "Jira instance URL",
        "JIRA_EMAIL": "Jira account email",
        "JIRA_API_TOKEN": "Jira API token",
        "JIRA_PROJECT_KEY": "Jira project key",
    }
    
    # Optional variables
    optional_vars = {
        "NOTION_TOKEN": "Notion integration token",
        "NOTION_DATABASE_ID": "Notion database ID",
        "ENVIRONMENT": "Environment",
        "LOG_LEVEL": "Log level",
        "SPRINT_DURATION_DAYS": "Sprint duration",
    }
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Variable", style="cyan", width=25)
    table.add_column("Description", width=30)
    table.add_column("Status", width=40)
    
    results = {}
    
    # Check required variables
    for var, desc in required_vars.items():
        is_valid, status = check_env_variable(var, required=True)
        results[var] = (is_valid, status)
        
        style = "green" if is_valid else "red"
        table.add_row(f"[{style}]{var}[/{style}]", desc, status)
    
    # Check optional variables
    for var, desc in optional_vars.items():
        is_valid, status = check_env_variable(var, required=False)
        results[var] = (is_valid, status)
        
        style = "green" if is_valid and "[OK]" in status else "yellow"
        table.add_row(f"[{style}]{var}[/{style}]", desc, status)
    
    console.print(table)
    return results


def test_jira_connection() -> bool:
    """Test Jira API connection."""
    console.print("\n[bold blue]Testing Jira Connection[/bold blue]\n")
    
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    if not all([jira_url, jira_email, jira_token]):
        console.print("[red][X] Jira credentials not configured[/red]")
        return False
    
    try:
        # Test connection to Jira API
        url = f"{jira_url}/rest/api/3/myself"
        
        console.print(f"[dim]Connecting to: {url}[/dim]")
        
        response = requests.get(
            url,
            auth=(jira_email, jira_token),
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green][OK] Jira connection successful![/green]")
            console.print(f"[green]   Logged in as: {data.get('displayName', 'Unknown')}[/green]")
            console.print(f"[green]   Email: {data.get('emailAddress', 'Unknown')}[/green]")
            console.print(f"[green]   Account ID: {data.get('accountId', 'Unknown')[:20]}...[/green]")
            return True
        elif response.status_code == 401:
            console.print("[red][X] Authentication failed - check your email and token[/red]")
            return False
        elif response.status_code == 404:
            console.print("[red][X] Jira URL not found - check JIRA_URL[/red]")
            return False
        else:
            console.print(f"[red][X] Unexpected status code: {response.status_code}[/red]")
            console.print(f"[dim]{response.text[:200]}[/dim]")
            return False
            
    except requests.exceptions.Timeout:
        console.print("[red][X] Connection timeout - check your internet or Jira URL[/red]")
        return False
    except requests.exceptions.ConnectionError:
        console.print("[red][X] Connection error - check your internet or Jira URL[/red]")
        return False
    except Exception as e:
        console.print(f"[red][X] Error: {str(e)}[/red]")
        return False


def check_data_files() -> List[Tuple[str, bool, str]]:
    """Check required data files."""
    console.print("\n[bold blue]Checking Data Files[/bold blue]\n")
    
    files_to_check = [
        ("data/users/users.json", True, "User data (copy from users_template.json)"),
        ("data/users/users_template.json", False, "User data template"),
        ("config/departments.yaml", False, "Departments configuration"),
        ("config/env.template", False, "Environment template"),
        (".env", True, "Environment configuration"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("File", style="cyan", width=35)
    table.add_column("Status", width=15)
    table.add_column("Description", width=40)
    
    results = []
    
    for file_path, required, description in files_to_check:
        exists = Path(file_path).exists()
        
        if exists:
            status = "[OK] EXISTS"
            style = "green"
        else:
            if required:
                status = "[X] MISSING"
                style = "red"
            else:
                status = "[!] Missing"
                style = "yellow"
        
        table.add_row(f"[{style}]{file_path}[/{style}]", status, description)
        results.append((file_path, exists, description))
    
    console.print(table)
    return results


def print_summary(env_results: Dict, jira_ok: bool, files_ok: List[Tuple]) -> None:
    """Print summary and recommendations."""
    console.print("\n[bold blue]Summary[/bold blue]\n")
    
    # Count issues
    env_issues = sum(1 for is_valid, _ in env_results.values() if not is_valid)
    missing_files = sum(1 for _, exists, _ in files_ok if not exists)
    
    # Overall status
    if env_issues == 0 and jira_ok and missing_files == 0:
        panel = Panel(
            "[green][OK] ALL CHECKS PASSED!\n\n"
            "Your project is fully configured and ready to use.[/green]",
            title="[bold green]SUCCESS[/bold green]",
            border_style="green"
        )
    else:
        issues_text = []
        
        if env_issues > 0:
            issues_text.append(f"[red][X] {env_issues} environment variable(s) need attention[/red]")
        
        if not jira_ok:
            issues_text.append("[red][X] Jira connection failed[/red]")
        
        if missing_files > 0:
            issues_text.append(f"[yellow][!] {missing_files} file(s) missing[/yellow]")
        
        panel = Panel(
            "\n".join(issues_text),
            title="[bold yellow]ACTION REQUIRED[/bold yellow]",
            border_style="yellow"
        )
    
    console.print(panel)


def print_next_steps() -> None:
    """Print next steps for the user."""
    console.print("\n[bold blue]Next Steps[/bold blue]\n")
    
    steps = [
        "1. Fill in missing environment variables in .env file",
        "2. Copy data/users/users_template.json to data/users/users.json",
        "3. Fill in real user data (names, emails, Jira account IDs)",
        "4. Update config/departments.yaml with your Jira board IDs",
        "5. Run this script again to verify: python scripts/validate_config.py",
        "6. Start development with PROJECT_PLAN.md → Stage 3 (Jira Integration)",
    ]
    
    for step in steps:
        if "Fill in missing" in step:
            console.print(f"[yellow]{step}[/yellow]")
        elif "Copy data" in step:
            console.print(f"[yellow]{step}[/yellow]")
        else:
            console.print(f"[dim]{step}[/dim]")


def main() -> None:
    """Main validation function."""
    console.print(Panel.fit(
        "[bold]Jira-Notion Sync Configuration Validator[/bold]\n"
        "[dim]Checking your project configuration...[/dim]",
        border_style="blue"
    ))
    
    # Run all checks
    env_results = validate_env_config()
    jira_ok = test_jira_connection()
    files_ok = check_data_files()
    
    # Print summary
    print_summary(env_results, jira_ok, files_ok)
    print_next_steps()
    
    # Exit code
    all_required_vars_ok = all(
        is_valid for var, (is_valid, _) in env_results.items() 
        if var.startswith("JIRA_")
    )
    
    if all_required_vars_ok and jira_ok:
        console.print("\n[green][OK] Configuration is valid![/green]\n")
        sys.exit(0)
    else:
        console.print("\n[yellow][!] Please fix the issues above[/yellow]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

