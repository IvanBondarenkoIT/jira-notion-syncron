"""Check what Notion fields are used and what might be missing."""

import os
import sys
from pathlib import Path
from collections import Counter

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import requests

load_dotenv()
console = None

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
except ImportError:
    pass


def print_msg(msg):
    """Print message."""
    if console:
        console.print(msg)
    else:
        print(msg)


def main():
    """Check Notion fields usage."""
    if console:
        console.print(Panel.fit(
            "[bold]Notion Fields Usage Analysis[/bold]",
            border_style="blue"
        ))
    else:
        print("=== Notion Fields Usage Analysis ===\n")
    
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db_id = os.getenv("NOTION_DATABASE_ID")
    
    if not all([notion_token, notion_db_id]):
        print_msg("Error: Notion credentials not configured")
        return
    
    # Fetch all pages
    url = f"https://api.notion.com/v1/databases/{notion_db_id}/query"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    print_msg("\n[blue]Fetching all pages from Notion...[/blue]\n")
    
    all_pages = []
    has_more = True
    start_cursor = None
    
    while has_more:
        payload = {}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print_msg(f"Error: {response.status_code} - {response.text[:200]}")
            return
        
        data = response.json()
        all_pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    
    print_msg(f"[green]Found {len(all_pages)} pages[/green]\n")
    
    # Analyze field usage
    field_usage = {
        "Task name": 0,
        "Status": 0,
        "Assignee (people)": 0,
        "Priority": 0,
        "Effort level": 0,
        "Due date": 0,
        "Date": 0,
        "Task type": 0,
        "Has icon/emoji": 0,
        "Has created_time": 0,
        "Has last_edited_time": 0,
    }
    
    date_examples = []
    due_date_examples = []
    icons = Counter()
    
    for page in all_pages:
        props = page.get("properties", {})
        
        # Task name
        title_prop = props.get("Task name", {})
        if title_prop.get("title"):
            field_usage["Task name"] += 1
        
        # Status
        status_prop = props.get("Status", {})
        if status_prop.get("status"):
            field_usage["Status"] += 1
        
        # Assignee
        for prop_value in props.values():
            if prop_value.get("type") == "people" and prop_value.get("people"):
                field_usage["Assignee (people)"] += 1
                break
        
        # Priority
        priority_prop = props.get("Priority", {})
        if priority_prop.get("select"):
            field_usage["Priority"] += 1
        
        # Effort level
        effort_prop = props.get("Effort level", {})
        if effort_prop.get("select"):
            field_usage["Effort level"] += 1
        
        # Due date
        due_prop = props.get("Due date", {})
        if due_prop.get("date"):
            field_usage["Due date"] += 1
            due_date_examples.append(due_prop.get("date", {}).get("start", ""))
        
        # Date
        date_prop = props.get("Date", {})
        if date_prop.get("date"):
            field_usage["Date"] += 1
            date_examples.append(date_prop.get("date", {}).get("start", ""))
        
        # Task type
        tags_prop = props.get("Task type", {})
        if tags_prop.get("multi_select"):
            field_usage["Task type"] += 1
        
        # Icon
        if page.get("icon"):
            field_usage["Has icon/emoji"] += 1
            icon = page.get("icon", {})
            if icon.get("type") == "emoji":
                icons[icon.get("emoji", "")] += 1
        
        # Timestamps
        if page.get("created_time"):
            field_usage["Has created_time"] += 1
        if page.get("last_edited_time"):
            field_usage["Has last_edited_time"] += 1
    
    # Display results
    if console:
        table = Table(show_header=True, header_style="bold cyan", show_lines=True)
        table.add_column("Field", style="yellow", width=25)
        table.add_column("Used", style="green", justify="right", width=10)
        table.add_column("Total", style="blue", justify="right", width=10)
        table.add_column("Usage %", style="magenta", justify="right", width=10)
        table.add_column("Extracted?", style="cyan", width=12)
        
        extracted_fields = {
            "Task name": "YES",
            "Status": "YES",
            "Assignee (people)": "YES",
            "Priority": "YES",
            "Effort level": "YES (desc)",
            "Due date": "YES",
            "Date": "NO",
            "Task type": "YES (tags)",
            "Has icon/emoji": "NO",
            "Has created_time": "NO",
            "Has last_edited_time": "NO",
        }
        
        for field, count in field_usage.items():
            usage_pct = (count / len(all_pages) * 100) if all_pages else 0
            extracted = extracted_fields.get(field, "?")
            
            table.add_row(
                field,
                str(count),
                str(len(all_pages)),
                f"{usage_pct:.1f}%",
                f"[green]{extracted}[/green]" if extracted.startswith("YES") else f"[red]{extracted}[/red]"
            )
        
        console.print(table)
    else:
        print("\nField Usage:")
        for field, count in field_usage.items():
            usage_pct = (count / len(all_pages) * 100) if all_pages else 0
            print(f"  {field:30s}: {count:3d}/{len(all_pages)} ({usage_pct:.1f}%)")
    
    # Show details
    print_msg("\n[bold]Analysis:[/bold]\n")
    
    if field_usage["Date"] > 0:
        print_msg(f"[yellow]'Date' field is used in {field_usage['Date']} tasks but NOT extracted![/yellow]")
        print_msg(f"[dim]Examples: {', '.join(date_examples[:3])}[/dim]\n")
    else:
        print_msg("[green]'Date' field is empty in all tasks - OK to skip[/green]\n")
    
    if field_usage["Has icon/emoji"] > 0:
        print_msg(f"[yellow]Icons/Emoji are present in {field_usage['Has icon/emoji']} tasks but NOT extracted[/yellow]")
        # Skip emoji display to avoid encoding issues
        print_msg(f"[dim]Found {len(icons)} different icons[/dim]\n")
    
    print_msg("[bold cyan]Recommendations:[/bold cyan]\n")
    
    recommendations = []
    
    if field_usage["Date"] > 0:
        recommendations.append("1. Extract 'Date' field (if different from Due date)")
    
    if field_usage["Has icon/emoji"] > 0:
        recommendations.append("2. Extract emoji icons and add as labels or in description")
    
    recommendations.append("3. Add created_time and last_edited_time to task description")
    
    if not recommendations:
        print_msg("[green]All important fields are being extracted![/green]")
    else:
        for rec in recommendations:
            print_msg(f"  {rec}")
    
    print_msg("\n[bold green]Summary:[/bold green]")
    extracted_count = sum(1 for v in extracted_fields.values() if v.startswith("YES"))
    print_msg(f"  Extracting: {extracted_count}/{len(extracted_fields)} available fields")
    print_msg(f"  Missing data: {len(recommendations)} potential improvements\n")


if __name__ == "__main__":
    main()

