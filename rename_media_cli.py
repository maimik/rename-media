#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Программа для переименования фото и видео файлов по дате съёмки
Версия: 1.1
Автор: Claude Sonnet 4.5
Дата: 2026-01-21
Обновление: 2026-01-22 (добавлено обнаружение переименованных файлов)
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
import subprocess
import json
from typing import Optional, Tuple, List

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("❌ Ошибка: не установлена библиотека Pillow")
    print("Установите её командой: pip install Pillow")
    sys.exit(1)

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

# Полный список поддерживаемых форматов фото (26 расширений)
PHOTO_EXTENSIONS = {
    # JPEG форматы
    '.jpg', '.jpeg', '.jpe', '.jfif',
    # PNG
    '.png',
    # GIF
    '.gif',
    # Bitmap
    '.bmp', '.dib',
    # TIFF
    '.tif', '.tiff',
    # WebP
    '.webp',
    # HEIF (iPhone)
    '.heic', '.heif',
    # RAW форматы
    '.raw', '.cr2', '.nef', '.arw',  # Canon, Nikon, Sony
    '.dng', '.orf', '.rw2',          # Adobe, Olympus, Panasonic
    # Другие
    '.psd',   # Photoshop
    '.ico',   # Icon
    '.pcx',   # PC Paintbrush
    '.tga'    # Targa
}

# Полный список поддерживаемых форматов видео (23 расширения)
VIDEO_EXTENSIONS = {
    # MPEG-4
    '.mp4', '.m4v', '.m4p',
    # QuickTime
    '.mov', '.qt',
    # AVI
    '.avi',
    # Windows Media
    '.wmv', '.asf',
    # Flash Video
    '.flv', '.f4v',
    # Matroska
    '.mkv',
    # WebM
    '.webm',
    # MPEG
    '.mpg', '.mpeg', '.mpe',
    # 3GPP (мобильные телефоны)
    '.3gp', '.3g2',
    # DVD Video
    '.vob',
    # Ogg Video
    '.ogv',
    # AVCHD
    '.mts', '.m2ts',
    # Transport Stream
    '.ts'
}

# Правильный формат даты (ISO 8601): год-месяц-день_часминутсекунд
DATE_FORMAT = "%Y-%m-%d_%H%M%S"

# Регулярное выражение для проверки уже переименованных файлов
# Формат: Photo-YYYY-MM-DD_HHMMSS[_N].ext или Video-YYYY-MM-DD_HHMMSS[_N].ext
RENAMED_PATTERN = re.compile(
    r'^(Photo|Video)-(\d{4})-(\d{2})-(\d{2})_(\d{6})(_\d+)?\.(\w+)$',
    re.IGNORECASE
)

# =============================================================================
# ФУНКЦИИ ДЛЯ ИЗВЛЕЧЕНИЯ ДАТЫ ИЗ МЕТАДАННЫХ
# =============================================================================

def is_already_renamed(filename: str) -> Tuple[bool, str]:
    """
    Проверить, соответствует ли имя файла шаблону переименования.
    
    Args:
        filename: имя файла (без пути)
    
    Returns:
        (True, "Photo"/"Video") если соответствует шаблону
        (False, "") если не соответствует
    
    Examples:
        >>> is_already_renamed("Photo-2023-08-15_142203.jpg")
        (True, "Photo")
        >>> is_already_renamed("IMG_20230815.jpg")
        (False, "")
    """
    match = RENAMED_PATTERN.match(filename)
    if match:
        prefix = match.group(1)  # "Photo" или "Video"
        return True, prefix
    return False, ""

def get_photo_creation_date(file_path: str) -> Optional[datetime]:
    """
    Извлечь дату создания фото из EXIF метаданных.

    Приоритет поиска:
    1. DateTimeOriginal (дата съёмки)
    2. DateTime (дата создания)
    3. CreateDate

    Args:
        file_path: путь к файлу изображения

    Returns:
        объект datetime или None если метаданные не найдены
    """
    try:
        with Image.open(file_path) as image:
            # Получаем EXIF данные
            exifdata = image._getexif()

            if not exifdata:
                return None

            # Приоритетные теги для поиска
            priority_tags = ['DateTimeOriginal', 'DateTime', 'CreateDate']

            # Создаём словарь тег:значение
            exif_dict = {TAGS.get(tag_id, tag_id): value
                        for tag_id, value in exifdata.items()}

            # Ищем по приоритету
            for tag_name in priority_tags:
                if tag_name in exif_dict:
                    date_str = exif_dict[tag_name]

                    # Обработка разных форматов дат
                    try:
                        # Стандартный формат EXIF: "2023:08:15 14:22:03"
                        return datetime.strptime(date_str[:19], '%Y:%m:%d %H:%M:%S')
                    except (ValueError, TypeError):
                        try:
                            # Альтернативный формат: "2023-08-15 14:22:03"
                            return datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
                        except (ValueError, TypeError):
                            continue

    except Exception as e:
        # Если файл повреждён или формат не поддерживается PIL
        pass

    return None


def check_ffprobe_available() -> bool:
    """Проверить доступность ffprobe в системе."""
    try:
        subprocess.run(['ffprobe', '-version'],
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_video_creation_date(file_path: str) -> Optional[datetime]:
    """
    Извлечь дату создания видео через ffprobe.

    Args:
        file_path: путь к видео файлу

    Returns:
        объект datetime или None если метаданные не найдены
    """
    try:
        # Команда ffprobe для получения метаданных
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_entries', 'format_tags=creation_time',
            file_path
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)

            # Извлекаем creation_time
            if 'format' in data and 'tags' in data['format']:
                creation_time = data['format']['tags'].get('creation_time')

                if creation_time:
                    # Форматы: "2023-08-15T14:22:03.000000Z" или "2023-08-15 14:22:03"
                    try:
                        # Убираем микросекунды и Z
                        clean_time = creation_time.replace('Z', '').split('.')[0]

                        # Пробуем ISO формат
                        if 'T' in clean_time:
                            return datetime.fromisoformat(clean_time)
                        else:
                            return datetime.strptime(clean_time, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        pass

    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    return None


def get_file_creation_date(file_path: str) -> datetime:
    """
    Получить дату создания файла из файловой системы (fallback метод).

    Args:
        file_path: путь к файлу

    Returns:
        объект datetime с датой создания файла
    """
    stat = os.stat(file_path)

    # В Windows: st_ctime = дата создания
    # В Unix: st_ctime = дата последнего изменения метаданных
    # Используем минимальную из двух дат для надёжности
    creation_time = min(stat.st_ctime, stat.st_mtime)

    return datetime.fromtimestamp(creation_time)


def get_media_date(file_path: str, is_video: bool) -> Tuple[Optional[datetime], str]:
    """
    Получить дату медиафайла с указанием источника.

    Args:
        file_path: путь к файлу
        is_video: True если это видео, False если фото

    Returns:
        кортеж (datetime, источник_даты)
    """
    # Пытаемся извлечь из метаданных
    if is_video:
        date = get_video_creation_date(file_path)
        if date:
            return date, "metadata"
    else:
        date = get_photo_creation_date(file_path)
        if date:
            return date, "EXIF"

    # Fallback на дату файла
    date = get_file_creation_date(file_path)
    return date, "file_system"


# =============================================================================
# ФУНКЦИИ ДЛЯ ПЕРЕИМЕНОВАНИЯ ФАЙЛОВ
# =============================================================================

def generate_new_filename(prefix: str, date: datetime, extension: str,
                         base_dir: str) -> str:
    """
    Сгенерировать новое имя файла, избегая дубликатов.

    Args:
        prefix: "Photo" или "Video"
        date: дата для форматирования
        extension: расширение файла (с точкой)
        base_dir: директория где будет файл

    Returns:
        новое имя файла (без пути)
    """
    # Базовое имя
    date_str = date.strftime(DATE_FORMAT)
    new_name = f"{prefix}-{date_str}{extension}"
    new_path = os.path.join(base_dir, new_name)

    # Если файл существует, добавляем счётчик
    counter = 1
    while os.path.exists(new_path):
        new_name = f"{prefix}-{date_str}_{counter}{extension}"
        new_path = os.path.join(base_dir, new_name)
        counter += 1

    return new_name


def process_file(file_path: str, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Обработать один файл: определить дату и переименовать.

    Args:
        file_path: полный путь к файлу
        dry_run: если True, не выполнять переименование, только показать что будет

    Returns:
        (успех, сообщение)
    """
    path_obj = Path(file_path)
    ext = path_obj.suffix.lower()

    # Определяем тип файла
    if ext in PHOTO_EXTENSIONS:
        prefix = "Photo"
        is_video = False
    elif ext in VIDEO_EXTENSIONS:
        prefix = "Video"
        is_video = True
    else:
        return False, f"[?] Пропущен (неподдерживаемый формат): {path_obj.name}"

    # Получаем дату
    date, source = get_media_date(str(file_path), is_video)

    if not date:
        return False, f"[X] Не удалось получить дату: {path_obj.name}"

    # Генерируем новое имя
    new_name = generate_new_filename(prefix, date, ext, str(path_obj.parent))

    # Проверка: если новое имя совпадает со старым
    # (это может произойти только если файл уже был правильно переименован
    # и пользователь явно выбрал "Переименовать заново")
    if new_name == path_obj.name:
        # В этом случае файл не нуждается в переименовании
        return False, f"[>] Уже имеет правильное имя: {path_obj.name}"

    # Формируем сообщение
    msg = f"{'[TEST]' if dry_run else '[+]'} {path_obj.name} -> {new_name} (дата: {source})"

    # Выполняем переименование
    if not dry_run:
        try:
            new_path = path_obj.parent / new_name
            os.rename(file_path, new_path)
        except Exception as e:
            return False, f"[X] Ошибка переименования {path_obj.name}: {e}"

    return True, msg


def scan_and_rename(root_folder: str, dry_run: bool = False, files_to_process: Optional[List[Path]] = None) -> dict:
    """
    Сканировать папку и переименовать все медиафайлы.

    Args:
        root_folder: путь к корневой папке
        dry_run: если True, только показать что будет изменено
        files_to_process: список файлов для обработки (если None, обрабатываются все)

    Returns:
        словарь со статистикой
    """
    root = Path(root_folder)

    if not root.is_dir():
        raise ValueError(f"Папка не существует: {root_folder}")

    stats = {
        'total': 0,
        'success': 0,
        'skipped': 0,
        'errors': 0,
        'messages': []
    }

    # Собираем все поддерживаемые расширения
    supported_exts = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS

    # Если список файлов не передан, собираем все файлы
    if files_to_process is None:
        # Сначала собираем все файлы и проверяем на уже переименованные
        all_files = []
        already_renamed = []
        
        for file_path in root.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                is_renamed, _ = is_already_renamed(file_path.name)
                if is_renamed:
                    already_renamed.append(file_path)
                else:
                    all_files.append(file_path)
        
        # Если найдены уже переименованные файлы, спрашиваем пользователя
        if already_renamed:
            print()
            print("╔" + "═" * 68 + "╗")
            print("║  ⚠️  ВНИМАНИЕ: Обнаружены уже переименованные файлы!" + " " * 13 + "║")
            print("╠" + "═" * 68 + "╣")
            print(f"║  Найдено: {len(already_renamed)} файлов соответствуют шаблону Photo/Video-YYYY-..." + " " * (68 - 66 - len(str(len(already_renamed)))) + "║")
            print("║" + " " * 68 + "║")
            print("║  Примеры:" + " " * 58 + "║")
            
            # Показываем до 5 примеров
            for i, file_path in enumerate(already_renamed[:5]):
                filename = file_path.name
                spaces = 68 - 7 - len(filename)
                print(f"║    • {filename}" + " " * spaces + "║")
            
            if len(already_renamed) > 5:
                remaining = len(already_renamed) - 5
                spaces = 68 - 11 - len(str(remaining))
                print(f"║    ... и ещё {remaining}" + " " * spaces + "║")
            
            print("╚" + "═" * 68 + "╝")
            print()
            print("[?] Что делать с этими файлами?")
            print("    [1] Пропустить (обработать только новые файлы)")
            print("    [2] Переименовать заново (на основе метаданных)")
            print("    [0] Отменить операцию")
            print()
            
            while True:
                choice = input("Ваш выбор (1/2/0): ").strip()
                
                if choice == '1':
                    # Пропускаем уже переименованные
                    files_to_process = all_files
                    print(f"\n[i] Будет обработано {len(files_to_process)} новых файлов")
                    print()
                    break
                elif choice == '2':
                    # Переименовываем все файлы
                    files_to_process = all_files + already_renamed
                    print(f"\n[i] Будет обработано {len(files_to_process)} файлов (включая уже переименованные)")
                    print()
                    break
                elif choice == '0':
                    # Отменяем операцию
                    print("\n[X] Операция отменена пользователем")
                    return stats
                else:
                    print("[!] Неверный выбор. Введите 1, 2 или 0")
        else:
            # Нет уже переименованных файлов
            files_to_process = all_files

    # Обрабатываем файлы
    for file_path in files_to_process:
        stats['total'] += 1

        success, message = process_file(str(file_path), dry_run)

        if success:
            stats['success'] += 1
        elif 'Пропущен' in message or 'Уже переименован' in message:
            stats['skipped'] += 1
        else:
            stats['errors'] += 1

        stats['messages'].append(message)
        print(message)

    return stats


# =============================================================================
# ГЛАВНАЯ ФУНКЦИЯ И CLI ИНТЕРФЕЙС
# =============================================================================

def print_banner():
    """Вывести баннер программы."""
    print("=" * 70)
    print("  Программа для переименования фото и видео по дате съёмки")
    print("  Версия 1.1 | 2026-01-22")
    print("  + Обнаружение уже переименованных файлов")
    print("=" * 70)
    print()


def print_help():
    """Вывести справку."""
    print("Использование:")
    print("  python rename_media_cli.py [путь_к_папке] [--test]")
    print()
    print("Параметры:")
    print("  путь_к_папке    Путь к папке с фото/видео (по умолчанию: текущая папка)")
    print("  --test          Тестовый режим (показать что будет изменено без реального переименования)")
    print()
    print(f"Поддерживаемые форматы фото ({len(PHOTO_EXTENSIONS)}):")
    print(f"  {', '.join(sorted(PHOTO_EXTENSIONS))}")
    print()
    print(f"Поддерживаемые форматы видео ({len(VIDEO_EXTENSIONS)}):")
    print(f"  {', '.join(sorted(VIDEO_EXTENSIONS))}")
    print()


def main():
    """Главная функция программы."""
    # Устанавливаем UTF-8 для Windows консоли
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    print_banner()

    # Парсинг аргументов
    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print_help()
        return 0

    # Определяем параметры
    dry_run = '--test' in args
    folder = '.'

    for arg in args:
        if not arg.startswith('--'):
            folder = arg
            break

    # Проверяем доступность ffprobe для видео
    has_ffprobe = check_ffprobe_available()

    if not has_ffprobe:
        print("[!] ПРЕДУПРЕЖДЕНИЕ: ffprobe не найден в системе.")
        print("    Для видео файлов будет использоваться дата из файловой системы.")
        print("    Установите ffmpeg для получения даты из метаданных видео:")
        print("    https://ffmpeg.org/download.html")
        print()

    # Выводим информацию
    print(f"[*] Папка для обработки: {os.path.abspath(folder)}")
    print(f"[*] Режим: {'ТЕСТ (без изменений)' if dry_run else 'РЕАЛЬНОЕ ПЕРЕИМЕНОВАНИЕ'}")
    print()

    if dry_run:
        print("[!] Тестовый режим: файлы не будут переименованы")
        print()
    else:
        response = input("[?] Вы уверены? Рекомендуется сделать резервную копию! (y/N): ")
        if response.lower() not in ['y', 'yes', 'д', 'да']:
            print("[X] Отменено пользователем")
            return 0
        print()

    # Запускаем обработку
    print("[*] Начинаем обработку...")
    print("-" * 70)

    try:
        stats = scan_and_rename(folder, dry_run)

        # Выводим статистику
        print("-" * 70)
        print()
        print("СТАТИСТИКА:")
        print(f"   Всего файлов обработано: {stats['total']}")
        print(f"   [+] Успешно переименовано: {stats['success']}")
        print(f"   [>] Пропущено: {stats['skipped']}")
        print(f"   [X] Ошибок: {stats['errors']}")
        print()

        if dry_run:
            print("[i] Запустите без параметра --test для реального переименования")
        else:
            print("[OK] Готово!")

        return 0

    except Exception as e:
        print()
        print(f"[X] КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
