# 📋 План развития проекта

## ✅ Этап 1: Инфраструктура (ЗАВЕРШЕН)

- [x] Создание структуры проекта (Clean Architecture)
- [x] Настройка виртуального окружения
- [x] Конфигурация линтеров и форматтеров
- [x] Настройка Docker
- [x] Создание Makefile
- [x] Pre-commit hooks
- [x] Документация (README, CONTRIBUTING, ADR)

## 🔄 Этап 2: Domain Models (ЗАВЕРШЕН)

- [x] User модель
- [x] Department модель
- [x] Task модель
- [x] Sprint модель
- [x] Unit тесты для моделей
- [x] Шаблоны данных (users, departments)

## 🚧 Этап 3: Jira Integration (СЛЕДУЮЩИЙ)

### 3.1 Repository Interface

```python
# src/domain/repositories/jira_repository.py
class JiraRepositoryInterface(ABC):
    def create_issue(self, task: Task) -> str
    def update_issue(self, issue_key: str, task: Task) -> None
    def get_issue(self, issue_key: str) -> Task
    def list_issues(self, project_key: str) -> List[Task]
```

### 3.2 Implementation

```python
# src/infrastructure/jira/jira_client.py
class JiraClient:
    """Jira API client."""
    
# src/infrastructure/jira/jira_repository.py
class JiraRepository(JiraRepositoryInterface):
    """Jira repository implementation."""
```

### 3.3 Use Cases

```python
# src/application/use_cases/create_jira_task.py
class CreateJiraTaskUseCase:
    """Create task in Jira."""
    
# src/application/use_cases/sync_jira_tasks.py
class SyncJiraTasksUseCase:
    """Sync tasks with Jira."""
```

**Задачи:**
- [ ] Реализовать Jira client
- [ ] Создать Jira repository
- [ ] Написать use cases
- [ ] Integration тесты с mock Jira API
- [ ] Обработка ошибок и retry logic

## 🚧 Этап 4: Notion Integration

### 4.1 Repository Interface

```python
# src/domain/repositories/notion_repository.py
class NotionRepositoryInterface(ABC):
    def get_database_items(self, database_id: str) -> List[Task]
    def create_page(self, database_id: str, task: Task) -> str
    def update_page(self, page_id: str, task: Task) -> None
```

### 4.2 Implementation

```python
# src/infrastructure/notion/notion_client.py
class NotionClient:
    """Notion API client."""
    
# src/infrastructure/notion/notion_repository.py
class NotionRepository(NotionRepositoryInterface):
    """Notion repository implementation."""
```

**Задачи:**
- [ ] Реализовать Notion client
- [ ] Создать Notion repository
- [ ] Парсинг Notion properties → Task модель
- [ ] Обработка разных типов полей (select, multi-select, date)
- [ ] Integration тесты

## 🚧 Этап 5: File Parsers

### 5.1 CSV Parser

```python
# src/infrastructure/parsers/csv_parser.py
class CSVParser:
    def parse(self, file_path: Path) -> List[Task]
```

### 5.2 Excel Parser

```python
# src/infrastructure/parsers/excel_parser.py
class ExcelParser:
    def parse(self, file_path: Path) -> List[Task]
```

### 5.3 Text Parser (Telegram)

```python
# src/infrastructure/parsers/text_parser.py
class TextParser:
    def parse(self, file_path: Path) -> List[Task]
    def extract_tasks(self, text: str) -> List[Task]
```

**Задачи:**
- [ ] CSV parser с валидацией
- [ ] Excel parser (openpyxl)
- [ ] Text parser с regex
- [ ] Определение формата автоматически
- [ ] Unit тесты с fixtures

## 🚧 Этап 6: Synchronization Logic

### 6.1 Sync Service

```python
# src/domain/services/sync_service.py
class SyncService:
    """Domain service for synchronization logic."""
    
    def merge_tasks(self, source: Task, target: Task) -> Task
    def detect_conflicts(self, tasks: List[Task]) -> List[Conflict]
    def deduplicate_tasks(self, tasks: List[Task]) -> List[Task]
```

### 6.2 Use Cases

```python
# src/application/use_cases/import_tasks.py
class ImportTasksUseCase:
    """Import tasks from various sources."""
    
# src/application/use_cases/sync_all.py
class SyncAllUseCase:
    """Synchronize all sources."""
```

**Задачи:**
- [ ] Дедупликация задач
- [ ] Мерж конфликтующих данных
- [ ] Приоритизация источников
- [ ] Транзакционность операций
- [ ] Rollback при ошибках

## 🚧 Этап 7: Sprint Management

### 7.1 Sprint Service

```python
# src/domain/services/sprint_service.py
class SprintService:
    """Service for sprint management."""
    
    def create_sprint(self, department_id: str) -> Sprint
    def start_sprint(self, sprint_id: str) -> None
    def complete_sprint(self, sprint_id: str) -> SprintReport
    def get_active_sprint(self, department_id: str) -> Optional[Sprint]
```

### 7.2 Use Cases

```python
# src/application/use_cases/create_weekly_sprint.py
class CreateWeeklySprintUseCase:
    """Create weekly sprint (7 days)."""
    
# src/application/use_cases/plan_sprint.py
class PlanSprintUseCase:
    """Plan sprint with tasks."""
```

**Задачи:**
- [ ] Автоматическое создание недельных спринтов
- [ ] Планирование задач в спринт
- [ ] Расчет velocity
- [ ] Sprint reports
- [ ] Синхронизация спринтов с Jira

## 🚧 Этап 8: Advanced CLI

### 8.1 Commands

```python
# sync - синхронизация
# import - импорт из файла
# export - экспорт данных
# sprint - управление спринтами
# users - управление пользователями
# stats - статистика
# config - конфигурация
```

### 8.2 Interactive Mode

```python
# Интерактивный режим с rich
# Выбор источников для синхронизации
# Просмотр конфликтов и их разрешение
# Progress bars для длительных операций
```

**Задачи:**
- [ ] Расширение команд CLI
- [ ] Интерактивный режим
- [ ] Progress bars
- [ ] Colored output
- [ ] Подробные error messages

## 🚧 Этап 9: Configuration Management

### 9.1 Settings

```python
# src/infrastructure/config/settings.py
class Settings(BaseSettings):
    """Application settings with validation."""
```

### 9.2 User/Department Management

```python
# Загрузка из JSON/YAML
# Валидация данных
# Кеширование
```

**Задачи:**
- [ ] Pydantic Settings
- [ ] Config validation
- [ ] Multiple environments (dev, prod)
- [ ] Secrets management

## 🚧 Этап 10: Logging & Monitoring

### 10.1 Structured Logging

```python
# JSON logging
# Different log levels per module
# Log rotation
```

### 10.2 Monitoring

```python
# Health checks
# Metrics collection
# Error tracking
```

**Задачи:**
- [ ] Structured logging (JSON)
- [ ] Log aggregation
- [ ] Performance metrics
- [ ] Error notifications (optional)

## 🚧 Этап 11: Advanced Features

### 11.1 Webhooks (Optional)

```python
# Webhook от Jira при изменении задач
# Webhook от Notion при обновлениях
```

### 11.2 Scheduled Sync

```python
# Cron jobs
# Windows Task Scheduler
# Continuous sync mode
```

### 11.3 API (Optional)

```python
# FastAPI REST API
# GraphQL endpoint
# WebSocket для real-time updates
```

**Задачи:**
- [ ] Webhook handlers
- [ ] Scheduler
- [ ] REST API (optional)

## 📊 Метрики успеха

### Качество кода
- [ ] Test coverage > 80%
- [ ] Mypy 100% coverage
- [ ] Zero linting errors
- [ ] Documentation coverage > 90%

### Функциональность
- [ ] Успешная синхронизация с Jira
- [ ] Успешная синхронизация с Notion
- [ ] Парсинг всех типов файлов
- [ ] Автоматическое создание спринтов
- [ ] Zero data loss

### Performance
- [ ] Синхронизация 1000 задач < 1 минуты
- [ ] Парсинг файла 10MB < 10 секунд
- [ ] API response time < 200ms

## 🎯 Приоритеты

### Must Have (P0)
1. Jira integration
2. File parsers (CSV, Excel, Text)
3. Basic sync logic
4. Sprint management
5. CLI interface

### Should Have (P1)
1. Notion integration
2. Advanced conflict resolution
3. Detailed logging
4. Error notifications

### Nice to Have (P2)
1. Webhooks
2. REST API
3. Real-time sync
4. Web UI

## 📅 Timeline (ориентировочно)

- **Этап 3**: 1-2 недели (Jira)
- **Этап 4**: 1 неделя (Notion)
- **Этап 5**: 1 неделя (Parsers)
- **Этап 6**: 1-2 недели (Sync Logic)
- **Этап 7**: 1 неделя (Sprints)
- **Этап 8**: 1 неделя (CLI)
- **Этапы 9-11**: 2-3 недели (Polish)

**Итого:** 8-11 недель для полной реализации

## 🔄 Итерации

Разработка ведется итеративно:

1. **MVP** (Минимальный продукт) - Этапы 3, 5, 6
2. **v1.0** (Первый релиз) - Этапы 3-8
3. **v2.0** (Полнофункциональный) - Этапы 9-11

---

**Текущий статус:** Этап 2 завершен ✅  
**Следующий шаг:** Начало Этапа 3 - Jira Integration 🚀

