"""Analyze Notion database structure.

Shows what properties exist in your Notion database.
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
    from rich.json import JSON
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv requests rich --quiet")
    from dotenv import load_dotenv
    import requests
    from rich.console import Console
    from rich.table import Table
    from rich.json import JSON

load_dotenv()
console = Console()


def get_notion_database_schema(database_id, notion_token):
    """Get database schema."""
    try:
        url = f"https://api.notion.com/v1/databases/{database_id}"
        
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            console.print(f"[red]Error: {response.status_code}[/red]")
            console.print(response.text[:500])
            return None
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None


def get_sample_pages(database_id, notion_token, limit=3):
    """Get sample pages."""
    try:
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        body = {"page_size": limit}
        
        response = requests.post(url, headers=headers, json=body, timeout=10)
        
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            console.print(f"[red]Error: {response.status_code}[/red]")
            return []
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return []


def main():
    """Analyze Notion database."""
    console.print("[bold blue]Analyzing Notion Database Structure[/bold blue]\n")
    
    notion_token = os.getenv("NOTION_TOKEN")
    notion_db_id = os.getenv("NOTION_DATABASE_ID")
    
    if not all([notion_token, notion_db_id]):
        console.print("[red]Error: Notion credentials not configured[/red]")
        return
    
    # Get database schema
    console.print("[blue]Fetching database schema...[/blue]\n")
    schema = get_notion_database_schema(notion_db_id, notion_token)
    
    if not schema:
        return
    
    # Show properties
    properties = schema.get("properties", {})
    
    console.print("[bold green]Database Properties:[/bold green]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Property Name", style="cyan", width=30)
    table.add_column("Type", style="yellow", width=20)
    table.add_column("Details", width=40)
    
    for prop_name, prop_data in properties.items():
        prop_type = prop_data.get("type", "unknown")
        
        details = ""
        if prop_type == "select":
            options = prop_data.get("select", {}).get("options", [])
            details = f"{len(options)} options"
        elif prop_type == "multi_select":
            options = prop_data.get("multi_select", {}).get("options", [])
            details = f"{len(options)} options"
        elif prop_type == "status":
            options = prop_data.get("status", {}).get("options", [])
            details = f"{len(options)} statuses"
        
        table.add_row(prop_name, prop_type, details)
    
    console.print(table)
    
    # Get sample pages
    console.print("\n[blue]Fetching sample pages...[/blue]\n")
    sample_pages = get_sample_pages(notion_db_id, notion_token, limit=2)
    
    if sample_pages:
        console.print(f"[bold green]Sample Page Structure (first page):[/bold green]\n")
        
        page = sample_pages[0]
        page_properties = page.get("properties", {})
        
        console.print("[bold]Properties with values:[/bold]\n")
        
        for prop_name, prop_data in page_properties.items():
            prop_type = prop_data.get("type", "unknown")
            
            # Extract value based on type
            value = "N/A"
            
            if prop_type == "title":
                titles = prop_data.get("title", [])
                if titles:
                    value = titles[0].get("plain_text", "")
            
            elif prop_type == "rich_text":
                texts = prop_data.get("rich_text", [])
                if texts:
                    value = texts[0].get("plain_text", "")
            
            elif prop_type == "select":
                select_data = prop_data.get("select")
                if select_data:
                    value = select_data.get("name", "")
            
            elif prop_type == "multi_select":
                multi = prop_data.get("multi_select", [])
                value = ", ".join([item.get("name", "") for item in multi])
            
            elif prop_type == "status":
                status_data = prop_data.get("status")
                if status_data:
                    value = status_data.get("name", "")
            
            elif prop_type == "date":
                date_data = prop_data.get("date")
                if date_data:
                    value = date_data.get("start", "")
            
            elif prop_type == "people":
                people = prop_data.get("people", [])
                if people:
                    value = ", ".join([p.get("name", "") for p in people])
            
            elif prop_type == "checkbox":
                value = str(prop_data.get("checkbox", False))
            
            elif prop_type == "number":
                value = str(prop_data.get("number", ""))
            
            console.print(f"[cyan]{prop_name}[/cyan] ({prop_type}): {value}")
        
        # Save to file for inspection
        output_file = project_root / "notion_sample.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sample_pages[0], f, indent=2, ensure_ascii=False)
        
        console.print(f"\n[green]Full sample saved to: notion_sample.json[/green]\n")
    
    console.print("\n[bold blue]Recommendations:[/bold blue]")
    console.print("1. Check the property names above")
    console.print("2. Update migrate_notion_to_jira.py with correct property names")
    console.print("3. Common properties to map:")
    console.print("   - Title/Name -> task title")
    console.print("   - Status -> task status")
    console.print("   - Assignee/Person -> assignee")
    console.print("   - Priority -> priority")
    console.print("   - Due Date/Date -> due date")
    console.print("   - Tags/Labels -> labels\n")


if __name__ == "__main__":
    main()








