"""Check updated task."""
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

# Check one of updated tasks
task_key = 'DG-157'
console.print(f"\n[bold cyan]Checking {task_key}...[/bold cyan]\n")

issue = client.get_issue(task_key)
console.print(f"[bold]Title:[/bold] {issue['fields']['summary']}")
console.print(f"[bold]Labels:[/bold] {', '.join(issue['fields'].get('labels', []))}")

desc = issue['fields'].get('description', {})
if desc and 'content' in desc:
    console.print(f"\n[bold]Description structure:[/bold]")
    console.print(f"  Total blocks: {len(desc['content'])}")
    
    console.print("\n[bold]Content blocks:[/bold]")
    for i, block in enumerate(desc['content'][:10], 1):
        block_type = block.get('type', 'unknown')
        
        if block_type == 'heading':
            level = block.get('attrs', {}).get('level', '?')
            text = ''
            if block.get('content'):
                text = block['content'][0].get('text', '')
            console.print(f"  {i}. Heading {level}: {text}")
        elif block_type == 'paragraph':
            text = ''
            if block.get('content'):
                text = block['content'][0].get('text', '')[:60]
            console.print(f"  {i}. Paragraph: {text}...")
        elif block_type == 'taskList':
            items = len(block.get('content', []))
            console.print(f"  {i}. Task List: {items} items")
        elif block_type == 'rule':
            console.print(f"  {i}. Divider")
        else:
            console.print(f"  {i}. {block_type}")
    
    if len(desc['content']) > 10:
        console.print(f"  ... and {len(desc['content']) - 10} more blocks")

client.close()

console.print("\n[bold green]Success! Task has been updated with full content![/bold green]")
console.print(f"\nView in Jira: {os.getenv('JIRA_URL')}/browse/{task_key}")







