# 🎯 Что делать дальше?

## ✅ Что уже сделано

Вы получили **профессиональный enterprise-grade проект** с:
- ✅ Clean Architecture структурой
- ✅ Domain моделями (User, Task, Sprint, Department)
- ✅ Полной настройкой линтеров и тестирования
- ✅ Docker контейнерами
- ✅ Детальной документацией

## 📝 Ваши следующие шаги

### Шаг 1: Установите зависимости (5 минут)

```powershell
# 1. Активируйте виртуальное окружение
venv\Scripts\activate

# 2. Установите все зависимости
pip install -r requirements-dev.txt

# 3. Настройте pre-commit hooks
pre-commit install

# 4. Проверьте что все работает
pytest tests/unit/ -v
```

### Шаг 2: Получите API ключи (10 минут)

#### Jira API Token
1. Откройте: https://id.atlassian.com/manage-profile/security/api-tokens
2. Нажмите **"Create API token"**
3. Дайте имя: "Jira Sync Integration"
4. Скопируйте токен (он больше не покажется!)

#### Notion Integration Token
1. Откройте: https://www.notion.so/my-integrations
2. Нажмите **"+ New integration"**
3. Дайте имя: "Jira Notion Sync"
4. Выберите workspace
5. Скопируйте **"Internal Integration Token"**
6. Откройте вашу базу данных в Notion
7. Нажмите **"..." → "Add connections"** → выберите вашу интеграцию

#### Notion Database ID
1. Откройте базу данных в Notion
2. URL будет: `https://notion.so/workspace/DATABASE_ID?v=...`
3. Скопируйте `DATABASE_ID` (32 символа)

### Шаг 3: Настройте конфигурацию (5 минут)

```powershell
# 1. Создайте .env файл
copy config\env.template .env

# 2. Откройте .env в редакторе и заполните:
```

```env
# Jira (заполните ваши данные)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token-here
JIRA_PROJECT_KEY=PROJ

# Notion (заполните ваши данные)
NOTION_TOKEN=secret_your-notion-token-here
NOTION_DATABASE_ID=your-32-char-database-id

# Настройки (можно оставить как есть)
ENVIRONMENT=development
LOG_LEVEL=INFO
SPRINT_DURATION_DAYS=7
SPRINT_START_DAY=monday
```

### Шаг 4: Настройте пользователей (10 минут)

```powershell
# 1. Создайте файл пользователей
copy data\users\users_template.json data\users\users.json

# 2. Откройте data\users\users.json и заполните реальными данными
```

**Как получить Jira Account ID:**
1. В Jira откройте профиль пользователя
2. URL будет: `https://your-domain.atlassian.net/jira/people/ACCOUNT_ID`
3. Скопируйте `ACCOUNT_ID`

**Как получить Notion User ID:**
1. В Notion API Explorer: https://developers.notion.com/reference/get-users
2. Или используйте API: `GET https://api.notion.com/v1/users`

**Пример заполненного файла:**
```json
{
  "users": [
    {
      "id": "user_001",
      "name": "Саша",
      "full_name": "Александр Иванов",
      "email": "sasha@company.com",
      "department": "marketing",
      "role": "marketing_specialist",
      "jira_account_id": "5b10a2844c20165700ede21g",
      "notion_user_id": "92a8d021-2e4c-4d5f-8c3a-9b3c2e1f4d5a",
      "active": true,
      "hire_date": "2024-01-15"
    },
    {
      "id": "user_002",
      "name": "Настя",
      "full_name": "Анастасия Петрова",
      "email": "nastya@company.com",
      "department": "marketing",
      "role": "marketing_specialist",
      "jira_account_id": "...",
      "notion_user_id": "...",
      "active": true
    },
    {
      "id": "user_003",
      "name": "Иван",
      "full_name": "Иван Сидоров",
      "email": "ivan@company.com",
      "department": "hr",
      "role": "hr_specialist",
      "jira_account_id": "...",
      "notion_user_id": "...",
      "active": true
    },
    {
      "id": "user_004",
      "name": "Директор",
      "full_name": "Директор Компании",
      "email": "director@company.com",
      "department": "management",
      "role": "director",
      "jira_account_id": "...",
      "notion_user_id": "...",
      "active": true
    }
  ]
}
```

### Шаг 5: Настройте отделы (5 минут)

Отредактируйте `config/departments.yaml`:

```yaml
departments:
  marketing:
    name: "Маркетинг"
    jira_board_id: "123"  # ← Замените на реальный ID доски
    notion_database_id: "abc123..."  # ← Замените на реальный ID базы
    members:
      - user_001  # Саша
      - user_002  # Настя
```

**Как получить Jira Board ID:**
1. Откройте доску в Jira
2. URL будет: `https://your-domain.atlassian.net/jira/software/c/projects/PROJ/boards/123`
3. Число `123` - это Board ID

### Шаг 6: Проверьте настройку (2 минуты)

```powershell
# Проверьте CLI
python -m src.presentation.cli.main --help

# Посмотрите пользователей
python -m src.presentation.cli.main users

# Посмотрите статистику
python -m src.presentation.cli.main stats
```

### Шаг 7: Положите ваши файлы с задачами

Положите файлы в папку `data/raw/`:

**CSV файлы:**
```
data/raw/tasks.csv
data/raw/marketing_tasks.csv
```

Формат CSV:
```csv
title,description,assignee,priority,department,due_date
"Создать контент-план","План на неделю","Саша","high","marketing","2024-10-25"
"Написать статью","Статья про продукт","Настя","medium","marketing","2024-10-26"
```

**Excel файлы:**
```
data/raw/tasks.xlsx
```

**Текстовые файлы (из Telegram):**
```
data/raw/telegram_messages.txt
```

## 🚀 Дальнейшая разработка

Теперь можно начинать разработку функционала!

### Рекомендуемый порядок:

**1. Jira Integration** (1-2 недели)
   - См. `PROJECT_PLAN.md` → Этап 3
   - Файлы: `src/infrastructure/jira/`

**2. File Parsers** (1 неделя)
   - CSV/Excel парсеры
   - Text парсер для Telegram
   - Файлы: `src/infrastructure/parsers/`

**3. Sync Logic** (1-2 недели)
   - Дедупликация задач
   - Мерж данных
   - Создание задач в Jira
   - Файлы: `src/application/use_cases/`

**4. Notion Integration** (1 неделя)
   - Опционально, если нужно
   - Файлы: `src/infrastructure/notion/`

## 📚 Полезные ресурсы

### Документация API
- 🔗 [Jira REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- 🔗 [Notion API Reference](https://developers.notion.com/reference/intro)

### Наша документация
- 📘 `README.md` - Полное описание проекта
- 📗 `QUICKSTART.md` - Быстрый старт
- 📙 `PROJECT_PLAN.md` - План развития на 11 этапов
- 📕 `CONTRIBUTING.md` - Гайд для разработчиков
- 📊 `PROJECT_OVERVIEW.md` - Обзор что уже сделано

## 💡 Полезные команды

```powershell
# Разработка
make help          # Показать все команды
make format        # Отформатировать код (black + isort)
make lint          # Проверить код (flake8 + pylint + mypy)
make test          # Запустить тесты с coverage
make clean         # Очистить временные файлы

# Docker
make docker-build  # Собрать Docker образ
make docker-up     # Запустить контейнер
make docker-logs   # Посмотреть логи

# Pre-commit
make pre-commit    # Запустить все проверки
```

## 🆘 Возникли проблемы?

### Ошибка: "Module not found"
```powershell
pip install -r requirements-dev.txt
```

### Ошибка: "Jira authentication failed"
- Проверьте JIRA_EMAIL и JIRA_API_TOKEN в .env
- Убедитесь что токен активен

### Ошибка: "Notion integration not found"
- Проверьте что база данных подключена к интеграции
- Проверьте NOTION_TOKEN в .env

### Тесты не проходят
```powershell
# Переустановите зависимости
pip install -r requirements-dev.txt

# Запустите тесты с подробным выводом
pytest tests/unit/ -v -s
```

## 📧 Что дальше?

После настройки:

1. ✅ Прочитайте `PROJECT_PLAN.md` - там детальный план
2. ✅ Начните с Этапа 3 (Jira Integration)
3. ✅ Используйте `CONTRIBUTING.md` для стандартов кода
4. ✅ Пишите тесты для всего нового кода

## 🎉 Готово!

У вас теперь есть **профессиональный базис** для проекта синхронизации.

**Вопросы?** Создайте Issue в репозитории или обратитесь к команде.

---

**Удачи в разработке! 🚀**

