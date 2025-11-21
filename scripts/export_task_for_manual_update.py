"""Export task content for manual update in Jira."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel

from src.infrastructure.notion.notion_storage import NotionStorage

console = Console()

TASK_TITLE = "Цветы на Батуми Молл"

# Load Notion data
storage = NotionStorage()
pages = storage.load_all_pages()

# Find the page
notion_page = None
for page in pages:
    if page.get_title().strip() == TASK_TITLE:
        notion_page = page
        break

if not notion_page:
    console.print(f"[red]Page not found![/red]")
    sys.exit(1)

console.print(Panel.fit(
    f"[bold]Содержимое для задачи: {TASK_TITLE}[/bold]",
    border_style="blue"
))

# Generate text for manual copy-paste
console.print("\n[bold green]═══ СКОПИРУЙТЕ ТЕКСТ НИЖЕ ═══[/bold green]\n")

print("h2. Описание задачи")
print()
print(notion_page.get_title())
print()

# Todos
todos = notion_page.get_todo_items()
if todos:
    print("h2. Чеклист")
    print()
    for todo in todos:
        checkbox = "(/) " if todo.checked else "(x) "
        print(f"{checkbox}{todo.get_plain_text()}")
    print()

# Images  
images = notion_page.get_images()
if images:
    print("h2. Изображения")
    print()
    for img in images:
        if img.file:
            print(f"!{img.file.url}|thumbnail!")
            caption = img.get_caption_text()
            if caption:
                print(f"_{caption}_")
    print()

# Metadata
print("----")
print("h3. Метаданные")
print()
status = notion_page.get_property_value("Status")
if status:
    print(f"*Статус в Notion:* {status}")

print(f"*Оригинал в Notion:* [{notion_page.url}|{notion_page.url}]")
print(f"*Обновлено:* {notion_page.last_edited_time.strftime('%Y-%m-%d')}")

console.print("\n[bold green]═══ КОНЕЦ ТЕКСТА ═══[/bold green]\n")

console.print("[yellow]Инструкция:[/yellow]")
console.print("1. Скопируйте весь текст между линиями ═══")
console.print("2. Откройте задачу DG-129 в Jira")
console.print("3. Нажмите Edit (редактировать)")
console.print("4. В поле Description вставьте скопированный текст")
console.print("5. Сохраните")
console.print()
console.print("[bold]Задача в Jira:[/bold]")
console.print("https://dimkavageorgia.atlassian.net/browse/DG-129")







