# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Проект

Программа для автоматического переименования фото и видео файлов по дате съёмки. Поддерживает 49 форматов (26 фото + 23 видео), имеет CLI и GUI интерфейсы, функцию Undo, пользовательские шаблоны и организацию по папкам.

## Установка и запуск

```bash
# Установка зависимостей
pip install -r requirements.txt
# или для разработки с тестами
pip install -e ".[dev]"

# Запуск GUI (рекомендуется для обычного использования)
python rename_media_gui.py

# Запуск CLI
python rename_media_cli.py "/путь/к/файлам" --test

# Тесты
python -m pytest
```

## Архитектура

### Основные модули

1. **rename_media_cli.py** - CLI интерфейс
   - Аргументы командной строки, основной цикл обработки
   - Константы: `PHOTO_EXTENSIONS`, `VIDEO_EXTENSIONS`, `DATE_FORMAT`, `RENAMED_PATTERN`

2. **rename_media_gui.py** - GUI интерфейс (tkinter)
   - Графический интерфейс для новичков
   - Многопоточность через `threading` и `queue` для неблокирующей обработки
   - Настройки: шаблоны, организация по папкам, функция Undo

3. **template_parser.py** - Парсер пользовательских шаблонов имён
   - Переменные: `{type}`, `{YYYY}`, `{YY}`, `{MM}`, `{DD}`, `{HH}`, `{hh}`, `{mm}`, `{ss}`, `{HHmmss}`
   - Метод `TemplateParser.format(date, file_type)` - генерация имени по шаблону

4. **folder_organizer.py** - Организация файлов по папкам
   - **ВАЖНО:** Пользователь должен иметь выбор режима группировки!
   - Режимы: `'none'` (без группировки), `'year'` (только по годам: `2023/`), `'year-month'` (по годам и месяцам: `2023/08/`), `'date'` (полная дата: `2023/08/15/`)
   - По умолчанию в GUI: `'year-month'` (наиболее популярный вариант)
   - Метод `FolderOrganizer(mode)` - принимает режим группировки
   - Метод `FolderOrganizer.get_folder_path(base_dir, date)` - получение пути для файла

5. **history_manager.py** - Управление историей операций (Undo)
   - Хранит до 10 операций в `.rename_history.json` (скрытый файл)
   - Методы: `record()`, `undo()`, `clear()`, `get_history()`

### Извлечение метаданных (приоритет)

**Фото** (`get_photo_creation_date()` в CLI/GUI):
1. EXIF DateTimeOriginal (дата съёмки)
2. EXIF DateTime (дата создания)
3. EXIF CreateDate
4. Fallback на дату файла

**Видео** (`get_video_creation_date()`):
1. ffprobe (creation_time из метаданных)
2. Fallback на дату файла

### Обработка дубликатов

Функция `generate_new_filename()` автоматически добавляет суффикс `_1`, `_2`, и т.д. при конфликте имён.

### Обнаружение уже переименованных файлов

`is_already_renamed(filename)` проверяет соответствие шаблону `Photo/Video-YYYY-MM-DD_HHMMSS[_N].ext`.

## Версионирование

Версия определяется в `pyproject.toml`. При изменении функционала обновите:
- `pyproject.toml` -> version
- `CHANGELOG.md` - добавьте новую секцию
- Копируйте версию в строки `__version__` в CLI/GUI (если есть)

## Тестирование

```bash
# Все тесты
python -m pytest

# С coverage
python -m pytest --cov=. --cov-report=html

# Конкретный тест
python -m pytest tests/test_renamed_check.py -v
```

## Создание EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=app_icon.ico --name="RenameMedia" rename_media_gui.py
```

## Важные детали

- Формат даты по умолчанию: `%Y-%m-%d_%H%M%S` (ISO 8601 compliant)
- История хранится в скрытом файле `.rename_history.json` в каждой обрабатываемой папке
- GUI использует `queue.Queue` для общения между главным потоком и рабочим потоком
- В Windows файл истории получает атрибут HIDDEN через `ctypes.windll.kernel32.SetFileAttributesW`

### Организация по папкам - выбор режима

При реализации группировки по папкам пользователь ДОЛЖЕН иметь выбор режима:

| Режим | Структура папок | Пример | Для кого |
|-------|-----------------|--------|----------|
| `none` | Без группировки | `Photo-2023-08-15...` | Не использует папки |
| `year` | Только годы | `2023/Photo-...` | Хочет простую структуру по годам |
| `year-month` | Годы + месяцы | `2023/08/Photo-...` | **Наиболее популярный** вариант |
| `date` | Полная дата | `2023/08/15/Photo-...` | Хочет максимальную детализацию |

**Важно:** В GUI должен быть выпадающий список (Combobox) или radio-кнопки для выбора режима. В CLI это параметр `--organize`.
