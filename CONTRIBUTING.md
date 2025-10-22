# 🤝 Contributing Guide

Спасибо за интерес к проекту! Этот документ содержит рекомендации по участию в разработке.

## 📋 Содержание

- [Процесс разработки](#процесс-разработки)
- [Настройка окружения](#настройка-окружения)
- [Стандарты кода](#стандарты-кода)
- [Тестирование](#тестирование)
- [Документация](#документация)
- [Pull Request Process](#pull-request-process)

## 🔄 Процесс разработки

### 1. Форкните репозиторий

```bash
git clone <your-fork>
cd jira-notion-syncron
```

### 2. Создайте feature branch

```bash
git checkout -b feature/your-feature-name
# или
git checkout -b fix/bug-description
```

### 3. Разработка

- Следуйте стандартам кода (см. ниже)
- Пишите тесты для нового функционала
- Обновляйте документацию при необходимости

### 4. Коммит

```bash
git add .
git commit -m "feat: добавлено новое feature"
```

**Формат коммитов** (Conventional Commits):

```
feat: новая функциональность
fix: исправление бага
docs: изменения в документации
style: форматирование кода
refactor: рефакторинг
test: добавление тестов
chore: обновление зависимостей, настройка CI/CD
```

### 5. Push и Pull Request

```bash
git push origin feature/your-feature-name
```

Создайте Pull Request с описанием изменений.

## 🛠️ Настройка окружения

### Базовая настройка

```bash
# Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Установите зависимости
make install-dev

# Настройте pre-commit hooks
make setup
```

### Проверка настройки

```bash
# Запустите тесты
make test

# Проверьте линтеры
make lint

# Отформатируйте код
make format
```

## 📝 Стандарты кода

### Python Code Style

Проект следует **PEP 8** с небольшими модификациями:

- Максимальная длина строки: **100 символов**
- Форматирование: **Black**
- Сортировка импортов: **isort**
- Линтинг: **Flake8**, **Pylint**
- Типизация: **mypy** (строгая проверка типов)

### Структура кода

```python
"""Module docstring."""

from typing import Optional

from pydantic import BaseModel, Field


class MyClass(BaseModel):
    """Class docstring.
    
    Attributes:
        field_name: Field description.
    """
    
    field_name: str = Field(..., description="Field description")
    
    def my_method(self, param: str) -> Optional[str]:
        """Method docstring.
        
        Args:
            param: Parameter description.
            
        Returns:
            Return value description.
        """
        return param
```

### Type Hints

Используйте type hints везде:

```python
from typing import Dict, List, Optional

def process_data(
    data: List[Dict[str, str]],
    filter_empty: bool = True
) -> Optional[List[str]]:
    """Process data with type hints."""
    ...
```

### Docstrings

Используйте **Google Style** docstrings:

```python
def function(arg1: str, arg2: int) -> bool:
    """Short description.
    
    Longer description if needed.
    
    Args:
        arg1: Description of arg1.
        arg2: Description of arg2.
        
    Returns:
        Description of return value.
        
    Raises:
        ValueError: When invalid input.
    """
    ...
```

## 🧪 Тестирование

### Требования к тестам

- **Покрытие**: минимум 80%
- **Типы**: unit, integration тесты
- **Фреймворк**: pytest

### Структура тестов

```
tests/
├── unit/           # Юнит-тесты
├── integration/    # Интеграционные тесты
├── fixtures/       # Тестовые данные
└── conftest.py     # Pytest конфигурация
```

### Написание тестов

```python
import pytest

from src.domain.models import User


class TestUser:
    """Tests for User model."""
    
    def test_user_creation(self) -> None:
        """Test user creation with valid data."""
        user = User(
            id="test_001",
            name="Test",
            email="test@example.com",
            department="marketing",
            role="marketing_specialist",
        )
        
        assert user.id == "test_001"
        assert user.is_active()
    
    def test_invalid_email(self) -> None:
        """Test user creation with invalid email."""
        with pytest.raises(ValidationError):
            User(
                id="test_001",
                name="Test",
                email="invalid",
                department="marketing",
                role="marketing_specialist",
            )
```

### Запуск тестов

```bash
# Все тесты
make test

# Только unit
make test-unit

# Только integration
make test-integration

# С покрытием
pytest --cov=src --cov-report=html
```

## 📚 Документация

### Обновление README

- Документируйте новые features
- Обновляйте примеры использования
- Добавляйте screenshots при необходимости

### ADR (Architecture Decision Records)

Для значительных архитектурных решений создавайте ADR в `docs/adr/`:

```markdown
# ADR-001: Выбор Clean Architecture

## Статус
Принято

## Контекст
Нужна была масштабируемая архитектура...

## Решение
Выбрали Clean Architecture потому что...

## Последствия
Положительные:
- ...

Отрицательные:
- ...
```

## 🔍 Code Review

### Что проверяем

- ✅ Код следует стандартам
- ✅ Есть тесты с хорошим покрытием
- ✅ Документация обновлена
- ✅ Pre-commit hooks проходят
- ✅ Нет конфликтов с main
- ✅ Понятные commit messages

### Процесс

1. Reviewer проверяет код
2. Запрашивает изменения если нужно
3. После исправлений - approve
4. Merge в main

## 📦 Pull Request Process

### Перед созданием PR

```bash
# Обновите main
git checkout main
git pull origin main

# Обновите свою ветку
git checkout feature/your-feature
git rebase main

# Запустите все проверки
make lint
make test
make pre-commit

# Убедитесь что все проходит
```

### Шаблон PR

```markdown
## Описание
Краткое описание изменений

## Тип изменений
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Чеклист
- [ ] Код следует стандартам проекта
- [ ] Написаны тесты
- [ ] Все тесты проходят
- [ ] Обновлена документация
- [ ] Pre-commit hooks проходят

## Связанные issues
Closes #123
```

## 🎨 Best Practices

### Clean Code

- **DRY** - Don't Repeat Yourself
- **SOLID** - Принципы объектно-ориентированного дизайна
- **KISS** - Keep It Simple, Stupid
- **YAGNI** - You Aren't Gonna Need It

### Git

- Маленькие, атомарные коммиты
- Понятные commit messages
- Feature branches
- Rebase вместо merge для чистой истории

### Python

- Use list comprehensions
- Use context managers (`with`)
- Use f-strings для форматирования
- Avoid mutable default arguments

## 🆘 Помощь

Если у вас возникли вопросы:

1. Прочитайте документацию
2. Проверьте существующие issues
3. Создайте новый issue с описанием проблемы

## 📜 Лицензия

Участвуя в разработке, вы соглашаетесь с тем, что ваш вклад будет лицензирован под MIT License.

---

**Спасибо за ваш вклад! 🎉**

