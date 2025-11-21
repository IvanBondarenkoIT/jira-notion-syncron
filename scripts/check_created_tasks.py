"""Check created tasks in Jira."""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from rich.console import Console

from src.infrastructure.jira.jira_client import JiraClient

load_dotenv()
console = Console()

client = JiraClient(
    os.getenv('JIRA_URL'),
    os.getenv('JIRA_EMAIL'),
    os.getenv('JIRA_API_TOKEN')
)

# Check a few created issues
test_keys = ['DG-94', 'DG-95', 'DG-96', 'DG-150']  # Last one with checklist

for key in test_keys:
    try:
        issue = client.get_issue(key)
        console.print(f"\n[bold blue]{key}[/bold blue]: {issue['fields']['summary']}")
        
        labels = issue['fields'].get('labels', [])
        console.print(f"Labels: {', '.join(labels)}")
        
        desc = issue['fields'].get('description', {})
        if desc and 'content' in desc:
            console.print(f"Description blocks: {len(desc['content'])}")
            
            # Show first few lines
            console.print("[dim]First content:[/dim]")
            for block in desc['content'][:3]:
                if block.get('content'):
                    for item in block['content'][:2]:
                        text = item.get('text', '')
                        if text:
                            console.print(f"  {text[:80]}")
        
    except Exception as e:
        console.print(f"[red]Error fetching {key}: {e}[/red]")

client.close()
console.print("\n[green]Done![/green]")







