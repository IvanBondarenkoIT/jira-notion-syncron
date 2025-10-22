# 🚀 Быстрый старт

Этот файл поможет вам начать работу с проектом за 5 минут.

## Шаг 1: Установка зависимостей

```powershell
# Активируйте виртуальное окружение
venv\Scripts\activate

# Установите зависимости
pip install -r requirements-dev.txt
```

## Шаг 2: Настройка конфигурации

### 2.1 Переменные окружения

Создайте файл `.env` в корне проекта:

```powershell
copy config\env.template .env
```

Отредактируйте `.env` и заполните:

```env
# Jira credentials
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token

# Notion credentials
NOTION_TOKEN=secret_your_token
NOTION_DATABASE_ID=your-database-id
```

### 2.2 Данные пользователей

Скопируйте шаблон и заполните данными:

```powershell
copy data\users\users_template.json data\users\users.json
```

Отредактируйте `data\users\users.json`:

```json
{
  "users": [
    {
      "id": "user_001",
      "name": "Саша",
      "full_name": "Александр",
      "email": "sasha@company.com",
      "department": "marketing",
      "role": "marketing_specialist",
      "jira_account_id": "ПОЛУЧИТЕ_ИЗ_JIRA",
      "notion_user_id": "ПОЛУЧИТЕ_ИЗ_NOTION",
      "active": true
    }
  ]
}
```

## Шаг 3: Получение API ключей

### Jira API Token

1. Перейдите: https://id.atlassian.com/manage-profile/security/api-tokens
2. Нажмите "Create API token"
3. Скопируйте токен в `.env` → `JIRA_API_TOKEN`

### Notion Integration Token

1. Перейдите: https://www.notion.so/my-integrations
2. Нажмите "+ New integration"
3. Дайте имя: "Jira Sync"
4. Скопируйте "Internal Integration Token" в `.env` → `NOTION_TOKEN`
5. Поделитесь базой данных с интеграцией

### Notion Database ID

1. Откройте вашу базу данных в Notion
2. URL будет выглядеть: `https://notion.so/workspace/DATABASE_ID?v=...`
3. Скопируйте `DATABASE_ID` в `.env` → `NOTION_DATABASE_ID`

## Шаг 4: Проверка установки

```powershell
# Запустите тесты
python -m pytest tests/unit/ -v

# Проверьте CLI
python -m src.presentation.cli.main --help
```

## Шаг 5: Первый запуск

### Просмотр пользователей

```powershell
python -m src.presentation.cli.main users
```

### Просмотр статистики

```powershell
python -m src.presentation.cli.main stats
```

### Dry-run синхронизация

```powershell
python -m src.presentation.cli.main sync --dry-run
```

## Структура данных

### Входные файлы

Положите файлы в `data/raw/`:

**CSV/Excel таблицы:**
```
data/raw/tasks.csv
data/raw/marketing_tasks.xlsx
```

**Текстовые файлы (из Telegram):**
```
data/raw/telegram_export.txt
```

Формат CSV:
```csv
title,description,assignee,priority,due_date
"Создать контент-план","Подготовить план на неделю","Саша","high","2024-10-25"
```

## Полезные команды (Makefile)

```powershell
# Посмотреть все команды
make help

# Форматирование кода
make format

# Проверка кода
make lint

# Запуск тестов
make test

# Очистка
make clean
```

## Docker (опционально)

```powershell
# Собрать образ
docker-compose build

# Запустить
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

## Следующие шаги

1. ✅ Заполните `data/users/users.json` реальными данными
2. ✅ Настройте `config/departments.yaml` под вашу структуру
3. ✅ Положите файлы с задачами в `data/raw/`
4. ✅ Запустите первую синхронизацию

## Troubleshooting

### Ошибка: "Module not found"

```powershell
# Убедитесь что виртуальное окружение активировано
venv\Scripts\activate

# Переустановите зависимости
pip install -r requirements-dev.txt
```

### Ошибка: "Jira authentication failed"

- Проверьте `JIRA_EMAIL` и `JIRA_API_TOKEN` в `.env`
- Убедитесь что токен активен
- Проверьте `JIRA_URL` (должен быть без `/` в конце)

### Ошибка: "Notion integration not found"

- Убедитесь что база данных подключена к интеграции
- Проверьте `NOTION_DATABASE_ID` (32 символа без дефисов)

## Дополнительная помощь

- 📖 Полная документация: [README.md](README.md)
- 🤝 Гайд для разработчиков: [CONTRIBUTING.md](CONTRIBUTING.md)
- 🏗️ Архитектурные решения: [docs/adr/](docs/adr/)

## Контакты

Если возникли вопросы - создайте Issue в репозитории.

---

**Готово! Теперь вы можете начать работу с проектом! 🎉**

