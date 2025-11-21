# Быстрая инструкция по развертыванию на другом компьютере

## Что нужно скопировать

### ✅ Обязательно скопировать:
1. **Весь репозиторий** (код проекта)
   ```bash
   git clone https://github.com/IvanBondarenkoIT/jira-notion-syncron.git
   cd jira-notion-syncron
   ```

2. **Видео файлы** (если нужны для обработки)
   - Скопируйте папку `data/input/videos/` с вашими `.mp4` файлами

### ❌ НЕ нужно копировать:
- `venv/` - виртуальное окружение (создастся заново)
- `data/models/` - модель Vosk (скачается автоматически)
- `data/processed/` - результаты обработки (создадутся заново)
- `.env` - файл с секретами (создайте заново)

## Пошаговая установка на новом компьютере

### 1. Установите Python 3.10+
Проверьте: `python --version` или `python3 --version`

### 2. Установите ffmpeg

**Windows:**
- Скачайте: https://www.gyan.dev/ffmpeg/builds/
- Распакуйте в `C:\ffmpeg\bin\`
- Добавьте путь к `bin` в системный PATH
- Перезапустите терминал

**Linux:**
```bash
sudo apt-get install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

### 3. Клонируйте репозиторий
```bash
git clone https://github.com/IvanBondarenkoIT/jira-notion-syncron.git
cd jira-notion-syncron
```

### 4. Создайте виртуальное окружение
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 5. Установите зависимости
```bash
# Для транскрибации (минимальный набор)
pip install vosk==0.3.45 soundfile==0.12.1 ffmpeg-python==0.2.0 rapidfuzz==3.9.7 loguru==0.7.2

# Или все зависимости проекта
pip install -r requirements.txt
```

### 6. Скопируйте видео файлы (если есть)
Поместите ваши `.mp4` файлы в `data/input/videos/`

### 7. Запустите транскрибацию
```bash
python scripts/transcribe_videos.py
```

При первом запуске автоматически скачается модель Vosk (~50 МБ).

### 8. Запустите анализ
```bash
python scripts/analyze_plans_reports.py
```

## Альтернатива: OpenAI Whisper (лучшее качество)

Если хотите использовать OpenAI Whisper вместо Vosk:

1. Получите API ключ: https://platform.openai.com/api-keys
2. Создайте `.env` файл:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
3. Установите пакет:
   ```bash
   pip install openai==1.51.0
   ```
4. Скрипт автоматически использует OpenAI

## Проверка установки

Проверьте, что все работает:
```bash
# Проверка ffmpeg
ffmpeg -version

# Проверка Python пакетов
python -c "import vosk; import rapidfuzz; print('OK')"

# Запуск транскрибации (если есть видео)
python scripts/transcribe_videos.py
```

## Структура папок после установки

```
jira-notion-syncron/
├── scripts/
│   ├── transcribe_videos.py      # Транскрибация
│   └── analyze_plans_reports.py  # Анализ
├── data/
│   ├── input/
│   │   └── videos/               # Ваши видео файлы
│   ├── processed/
│   │   ├── transcripts/          # Результаты транскрибации
│   │   └── analysis/             # Результаты анализа
│   └── models/                   # Модель Vosk (скачается автоматически)
├── venv/                         # Виртуальное окружение
└── requirements.txt              # Зависимости
```

## Подробная документация

См. `SETUP_TRANSCRIPTION.md` для детальной информации.

