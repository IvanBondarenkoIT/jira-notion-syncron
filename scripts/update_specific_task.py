"""Update specific task with full Notion content."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from rich.console import Console

from src.infrastructure.jira.jira_client import JiraClient
from src.infrastructure.notion.notion_storage import NotionStorage

load_dotenv()
console = Console()

# Task to update - we'll find it
TASK_TITLE = "Цветы на Батуми Молл"

# Load Notion data
console.print("\n[blue]Loading Notion data...[/blue]")
storage = NotionStorage()
pages = storage.load_all_pages()

# Find the page
notion_page = None
for page in pages:
    if page.get_title().strip() == TASK_TITLE:
        notion_page = page
        break

if not notion_page:
    console.print(f"[red]Page '{TASK_TITLE}' not found in Notion storage![/red]")
    sys.exit(1)

console.print(f"[green]Found Notion page![/green]")
console.print(f"  Blocks: {len(notion_page.blocks)}")
console.print(f"  Todos: {len(notion_page.get_todo_items())}")
console.print(f"  Images: {len(notion_page.get_images())}")

# Show todos
console.print("\n[bold]Todo items from Notion:[/bold]")
for todo in notion_page.get_todo_items():
    status = "✓" if todo.checked else "☐"
    console.print(f"  {status} {todo.get_plain_text()}")

# Connect to Jira
console.print("\n[blue]Connecting to Jira...[/blue]")
client = JiraClient(
    os.getenv('JIRA_URL'),
    os.getenv('JIRA_EMAIL'),
    os.getenv('JIRA_API_TOKEN')
)

# Search for task by checking each issue in range
console.print(f"[blue]Searching for task '{TASK_TITLE}'...[/blue]")
task_key = None
issue = None

for num in range(94, 200):
    try:
        test_key = f"DG-{num}"
        test_issue = client.get_issue(test_key)
        if TASK_TITLE in test_issue['fields']['summary']:
            task_key = test_key
            issue = test_issue
            break
    except:
        continue

if not task_key:
    console.print("[red]Task not found in Jira![/red]")
    client.close()
    sys.exit(1)

console.print(f"[green]Found task: {task_key}[/green]\n")

# Build ADF description
console.print("[blue]Building description...[/blue]")

content = []

# Header
content.append({
    "type": "heading",
    "attrs": {"level": 2},
    "content": [{"type": "text", "text": "Описание задачи"}]
})

# Content
page_content = notion_page.get_content_markdown()
if page_content and page_content.strip():
    content.append({
        "type": "paragraph",
        "content": [{"type": "text", "text": "Цветы на Батуми Молл"}]
    })

# Todo list as checklist
todos = notion_page.get_todo_items()
if todos:
    content.append({
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": "Чеклист"}]
    })
    
    task_items = []
    for todo in todos:
        task_items.append({
            "type": "taskItem",
            "attrs": {"state": "DONE" if todo.checked else "TODO"},
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": todo.get_plain_text()}]
            }]
        })
    
    content.append({
        "type": "taskList",
        "attrs": {"localId": "checklist-flowers"},
        "content": task_items
    })

# Images
images = notion_page.get_images()
if images:
    content.append({
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": "Изображения"}]
    })
    
    for img in images:
        if img.file:
            content.append({
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "🖼️ "},
                    {
                        "type": "text",
                        "text": "Фото цветов",
                        "marks": [{"type": "link", "attrs": {"href": img.file.url}}]
                    }
                ]
            })

# Metadata
content.append({"type": "rule"})
content.append({
    "type": "paragraph",
    "content": [
        {"type": "text", "text": "Импортировано из Notion • ", "marks": [{"type": "em"}]},
        {
            "type": "text",
            "text": "Оригинал",
            "marks": [
                {"type": "em"},
                {"type": "link", "attrs": {"href": notion_page.url}}
            ]
        }
    ]
})

# Status
status = notion_page.get_property_value("Status")
if status:
    content.append({
        "type": "paragraph",
        "content": [
            {"type": "text", "text": f"Статус в Notion: {status}", "marks": [{"type": "strong"}]}
        ]
    })

description_adf = {
    "type": "doc",
    "version": 1,
    "content": content
}

# Update labels
labels = issue['fields'].get('labels', [])
new_labels = list(set(labels + ['full-content-updated', 'has-checklist', 'has-images']))

# Update task
console.print(f"[yellow]Updating {task_key}...[/yellow]")

update_data = {
    "fields": {
        "description": description_adf,
        "labels": new_labels
    }
}

try:
    client.update_issue(task_key, update_data)
    console.print(f"\n[bold green]✓ Successfully updated {task_key}![/bold green]")
    console.print(f"\nView in Jira: {os.getenv('JIRA_URL')}/browse/{task_key}")
    console.print("\n[bold]What was added:[/bold]")
    console.print(f"  ✓ {len(todos)} todo items (checklist)")
    console.print(f"  ✓ {len(images)} image(s)")
    console.print(f"  ✓ Link to Notion page")
    console.print(f"  ✓ Status from Notion")
    
except Exception as e:
    console.print(f"\n[red]Error updating task: {e}[/red]")
    import traceback
    traceback.print_exc()

client.close()

