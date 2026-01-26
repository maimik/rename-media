#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Программа для переименования фото и видео файлов по дате съёмки (GUI версия)
Версия: 1.3
Автор: Claude Sonnet 4.5
Дата: 2026-01-21
Обновления:
  - 2026-01-22: добавлено обнаружение переименованных файлов
  - 2026-01-26: добавлены пользовательские шаблоны и группировка по папкам
"""

import os
import sys
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from datetime import datetime
from pathlib import Path
import subprocess
import json
import threading
import queue
from typing import Optional, Tuple, List

# Импорт новых модулей для v1.3
try:
    from template_parser import TemplateParser
    from folder_organizer import FolderOrganizer
except ImportError:
    # Если запущен через IDE или из другого места, пробуем относительный путь
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from template_parser import TemplateParser
    from folder_organizer import FolderOrganizer

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("❌ Ошибка: не установлена библиотека Pillow")
    print("Установите её командой: pip install Pillow")
    sys.exit(1)

# =============================================================================
# КОНФИГУРАЦИЯ (аналогична CLI версии)
# =============================================================================

PHOTO_EXTENSIONS = {
    '.jpg', '.jpeg', '.jpe', '.jfif', '.png', '.gif', '.bmp', '.dib',
    '.tif', '.tiff', '.webp', '.heic', '.heif', '.raw', '.cr2', '.nef',
    '.arw', '.dng', '.orf', '.rw2', '.psd', '.ico', '.pcx', '.tga'
}

VIDEO_EXTENSIONS = {
    '.mp4', '.m4v', '.m4p', '.mov', '.qt', '.avi', '.wmv', '.asf',
    '.flv', '.f4v', '.mkv', '.webm', '.mpg', '.mpeg', '.mpe',
    '.3gp', '.3g2', '.vob', '.ogv', '.mts', '.m2ts', '.ts'
}

DATE_FORMAT = "%Y-%m-%d_%H%M%S"

# Регулярное выражение для проверки уже переименованных файлов
# Формат: Photo-YYYY-MM-DD_HHMMSS[_N].ext или Video-YYYY-MM-DD_HHMMSS[_N].ext
RENAMED_PATTERN = re.compile(
    r'^(Photo|Video)-(\d{4})-(\d{2})-(\d{2})_(\d{6})(_\d+)?\.\w+$',
    re.IGNORECASE
)

# =============================================================================
# ФУНКЦИИ ДЛЯ ПРОВЕРКИ УЖЕ ПЕРЕИМЕНОВАННЫХ ФАЙЛОВ
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

# =============================================================================
# ФУНКЦИИ ДЛЯ ИЗВЛЕЧЕНИЯ МЕТАДАННЫХ (копия из CLI версии)
# =============================================================================

def get_photo_creation_date(file_path: str) -> Optional[datetime]:
    """Извлечь дату создания фото из EXIF метаданных."""
    try:
        with Image.open(file_path) as image:
            exifdata = image._getexif()
            if not exifdata:
                return None

            priority_tags = ['DateTimeOriginal', 'DateTime', 'CreateDate']
            exif_dict = {TAGS.get(tag_id, tag_id): value
                        for tag_id, value in exifdata.items()}

            for tag_name in priority_tags:
                if tag_name in exif_dict:
                    date_str = exif_dict[tag_name]
                    try:
                        return datetime.strptime(date_str[:19], '%Y:%m:%d %H:%M:%S')
                    except (ValueError, TypeError):
                        try:
                            return datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
                        except (ValueError, TypeError):
                            continue
    except Exception:
        pass
    return None


def get_video_creation_date(file_path: str) -> Optional[datetime]:
    """Извлечь дату создания видео через ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_entries', 'format_tags=creation_time', file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, timeout=30)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'format' in data and 'tags' in data['format']:
                creation_time = data['format']['tags'].get('creation_time')
                if creation_time:
                    clean_time = creation_time.replace('Z', '').split('.')[0]
                    if 'T' in clean_time:
                        return datetime.fromisoformat(clean_time)
                    else:
                        return datetime.strptime(clean_time, '%Y-%m-%d %H:%M:%S')
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def get_file_creation_date(file_path: str) -> datetime:
    """Получить дату создания файла из файловой системы."""
    stat = os.stat(file_path)
    creation_time = min(stat.st_ctime, stat.st_mtime)
    return datetime.fromtimestamp(creation_time)


def get_media_date(file_path: str, is_video: bool) -> Tuple[Optional[datetime], str]:
    """Получить дату медиафайла с указанием источника."""
    if is_video:
        date = get_video_creation_date(file_path)
        if date:
            return date, "metadata"
    else:
        date = get_photo_creation_date(file_path)
        if date:
            return date, "EXIF"

    date = get_file_creation_date(file_path)
    return date, "file_system"


def generate_new_filename(prefix: str, date: datetime, extension: str,
                         base_dir: str, template_parser: Optional[TemplateParser] = None) -> str:
    """Сгенерировать новое имя файла, избегая дубликатов."""
    if template_parser:
        new_name = template_parser.parse(prefix, date, extension)
    else:
        date_str = date.strftime(DATE_FORMAT)
        new_name = f"{prefix}-{date_str}{extension}"
    
    new_path = os.path.join(base_dir, new_name)

    if not os.path.exists(new_path):
        return new_name

    # Обработка дубликатов для шаблонов и стандартного формата
    name_stem = Path(new_name).stem
    counter = 1
    while os.path.exists(new_path):
        new_name = f"{name_stem}_{counter}{extension}"
        new_path = os.path.join(base_dir, new_name)
        counter += 1

    return new_name


def process_file(file_path: str, dry_run: bool = False,
                 template_parser: Optional[TemplateParser] = None,
                 folder_organizer: Optional[FolderOrganizer] = None) -> Tuple[bool, str]:
    """Обработать один файл: определить дату и переименовать."""
    path_obj = Path(file_path)
    ext = path_obj.suffix.lower()

    if ext in PHOTO_EXTENSIONS:
        prefix = "Photo"
        is_video = False
    elif ext in VIDEO_EXTENSIONS:
        prefix = "Video"
        is_video = True
    else:
        return False, f"❓ Пропущен: {path_obj.name}"

    date, source = get_media_date(str(file_path), is_video)

    if not date:
        return False, f"❌ Не удалось получить дату: {path_obj.name}"

    # Если включена организация по папкам, целевая папка меняется
    target_dir = path_obj.parent
    if folder_organizer:
        target_dir = folder_organizer.get_target_path(Path(file_path).parent, date)
        if not dry_run and not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

    new_name = generate_new_filename(prefix, date, ext, str(target_dir), template_parser)
    new_path = target_dir / new_name

    # Проверка: если путь не изменился
    if new_path == path_obj:
        return False, f"⏩ Уже имеет правильное имя и место: {path_obj.name}"

    msg = f"{'[ТЕСТ]' if dry_run else '✅'} {path_obj.name} → {new_name}"
    if folder_organizer and target_dir != path_obj.parent:
        try:
            rel_target = target_dir.relative_to(path_obj.parent)
            msg += f" (в {rel_target})"
        except ValueError:
            msg += f" (в {target_dir.name})"

    if not dry_run:
        try:
            os.rename(file_path, new_path)
        except Exception as e:
            return False, f"❌ Ошибка: {path_obj.name}: {e}"

    return True, msg


# =============================================================================
# GUI ПРИЛОЖЕНИЕ
# =============================================================================

class RenamedFilesDialog(tk.Toplevel):
    """
    Модальный диалог для отображения уже переименованных файлов
    и запроса действия у пользователя.
    """
    
    def __init__(self, parent: tk.Tk, renamed_files: List[Path], to_rename_count: int):
        """
        Args:
            parent: родительское окно
            renamed_files: список уже переименованных файлов
            to_rename_count: количество файлов, требующих переименования
        """
        super().__init__(parent)
        
        self.parent = parent
        self.renamed_files = renamed_files
        self.to_rename_count = to_rename_count
        self.result = None
        
        # Настройка окна
        self.title("⚠️ Обнаружены уже переименованные файлы")
        self.geometry("700x500")
        self.resizable(False, False)
        
        # Делаем окно модальным
        self.transient(parent)
        self.grab_set()
        
        # Создаём интерфейс
        self.create_widgets()
        
        # Центрируем окно
        self.center_window()
        
    def center_window(self):
        """Центрировать окно относительно родительского."""
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')
        
    def create_widgets(self):
        """Создать элементы интерфейса."""
        # Заголовок
        header_frame = tk.Frame(self, bg="#FFF3CD", pady=15)
        header_frame.pack(fill=tk.X)
        
        tk.Label(
            header_frame,
            text="⚠️ ВНИМАНИЕ: Обнаружены уже переименованные файлы!",
            font=("Arial", 12, "bold"),
            bg="#FFF3CD",
            fg="#856404"
        ).pack()
        
        # Информация
        info_frame = tk.Frame(self, pady=10)
        info_frame.pack(fill=tk.X, padx=20)
        
        info_text = (
            f"Найдено {len(self.renamed_files)} файлов, соответствующих шаблону:\n"
            f"Photo/Video-YYYY-MM-DD_HHMMSS\n\n"
            f"Также найдено {self.to_rename_count} файлов, требующих переименования."
        )
        
        tk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 10),
            justify=tk.LEFT
        ).pack(anchor="w")
        
        # Список файлов
        list_frame = tk.Frame(self, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        tk.Label(
            list_frame,
            text="Примеры обнаруженных файлов:",
            font=("Arial", 10, "bold"),
            anchor="w"
        ).pack(anchor="w")
        
        # Scrollable список
        list_container = tk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(
            list_container,
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set,
            height=12
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Заполняем список (максимум 100 файлов)
        for file_path in self.renamed_files[:100]:
            # Определяем иконку
            ext = file_path.suffix.lower()
            icon = "📷" if ext in PHOTO_EXTENSIONS else "🎬"
            self.file_listbox.insert(tk.END, f"{icon} {file_path.name}")
        
        if len(self.renamed_files) > 100:
            self.file_listbox.insert(tk.END, f"... и ещё {len(self.renamed_files) - 100} файлов")
        
        # Вопрос
        question_frame = tk.Frame(self, pady=10)
        question_frame.pack(fill=tk.X, padx=20)
        
        tk.Label(
            question_frame,
            text="Что делать с этими файлами?",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")
        
        # Кнопки
        button_frame = tk.Frame(self, pady=15)
        button_frame.pack(fill=tk.X, padx=20)
        
        btn_skip = tk.Button(
            button_frame,
            text="Пропустить",
            command=self.on_skip,
            font=("Arial", 10),
            width=18,
            height=2,
            bg="#28A745",
            fg="white",
            cursor="hand2"
        )
        btn_skip.pack(side=tk.LEFT, padx=5)
        
        btn_rerename = tk.Button(
            button_frame,
            text="Переименовать заново",
            command=self.on_rerename,
            font=("Arial", 10),
            width=18,
            height=2,
            bg="#FFC107",
            fg="black",
            cursor="hand2"
        )
        btn_rerename.pack(side=tk.LEFT, padx=5)
        
        btn_cancel = tk.Button(
            button_frame,
            text="Отмена",
            command=self.on_cancel,
            font=("Arial", 10),
            width=18,
            height=2,
            bg="#DC3545",
            fg="white",
            cursor="hand2"
        )
        btn_cancel.pack(side=tk.LEFT, padx=5)
        
        # Обработка закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
    def on_skip(self):
        """Пропустить уже переименованные файлы."""
        self.result = "skip"
        self.destroy()
        
    def on_rerename(self):
        """Переименовать заново все файлы."""
        self.result = "rerename"
        self.destroy()
        
    def on_cancel(self):
        """Отменить операцию."""
        self.result = "cancel"
        self.destroy()
        
    def get_result(self) -> str:
        """
        Получить результат выбора пользователя.
        
        Returns:
            "skip", "rerename", или "cancel"
        """
        return self.result


class RenameMediaApp:
    """Главное окно приложения."""

    def __init__(self, root):
        self.root = root
        self.root.title("Переименование фото и видео")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Переменные
        self.folder_path = ""
        self.is_processing = False
        self.dry_run = tk.BooleanVar(value=True)
        self.template_str = tk.StringVar(value=TemplateParser.DEFAULT_TEMPLATE)
        self.organize_folders = tk.BooleanVar(value=False)
        
        # Переменные для синхронизации с диалогом
        self.user_choice = None
        self.choice_queue = queue.Queue()

        # Создаём интерфейс
        self.create_widgets()

        # Центрируем окно
        self.center_window()

    def center_window(self):
        """Центрировать окно на экране."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Создать элементы интерфейса."""
        # Заголовок
        header = tk.Label(
            self.root,
            text="Переименование фото и видео по дате съёмки",
            font=("Arial", 14, "bold"),
            pady=10
        )
        header.pack()

        # Информация о форматах
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=5)

        tk.Label(
            info_frame,
            text=f"Поддерживается {len(PHOTO_EXTENSIONS)} форматов фото и {len(VIDEO_EXTENSIONS)} форматов видео",
            font=("Arial", 9),
            fg="gray"
        ).pack()

        # Фрейм выбора папки
        folder_frame = tk.Frame(self.root, pady=10)
        folder_frame.pack(fill=tk.X, padx=20)

        self.btn_select = tk.Button(
            folder_frame,
            text="📁 Выбрать папку",
            command=self.select_folder,
            font=("Arial", 12),
            height=2,
            width=20,
            bg="#4CAF50",
            fg="white",
            cursor="hand2"
        )
        self.btn_select.pack()

        # Метка выбранной папки
        self.label_selected = tk.Label(
            self.root,
            text="Папка не выбрана",
            font=("Arial", 10),
            wraplength=700,
            fg="gray"
        )
        self.label_selected.pack(pady=5)

        # Чекбокс тестового режима
        test_frame = tk.Frame(self.root)
        test_frame.pack(pady=5)

        self.check_test = tk.Checkbutton(
            test_frame,
            text="Тестовый режим (предпросмотр без изменений)",
            variable=self.dry_run,
            font=("Arial", 10)
        )
        self.check_test.pack()

        # Фрейм настроек шаблона и папок
        settings_frame = tk.LabelFrame(self.root, text="Настройки переименования", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, padx=20, pady=10)

        # Шаблон
        template_label_frame = tk.Frame(settings_frame)
        template_label_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            template_label_frame,
            text="Шаблон имени:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT)
        
        tk.Entry(
            template_label_frame,
            textvariable=self.template_str,
            font=("Consolas", 10),
            width=50
        ).pack(side=tk.LEFT, padx=10)

        tk.Label(
            settings_frame,
            text="Доступные теги: {prefix}, {YYYY}, {MM}, {DD}, {HH}, {mm}, {ss}, {ext}",
            font=("Arial", 8),
            fg="gray"
        ).pack(anchor="w")

        # Группировка по папкам
        self.check_folders = tk.Checkbutton(
            settings_frame,
            text="Группировать по папкам (Год/Месяц)",
            variable=self.organize_folders,
            font=("Arial", 10)
        )
        self.check_folders.pack(anchor="w", pady=5)

        # Кнопка запуска
        self.btn_run = tk.Button(
            self.root,
            text="▶️ Запустить переименование",
            state=tk.DISABLED,
            command=self.start_processing,
            font=("Arial", 12, "bold"),
            height=2,
            width=30,
            bg="#2196F3",
            fg="white",
            cursor="hand2"
        )
        self.btn_run.pack(pady=10)

        # Прогресс бар
        self.progress = ttk.Progressbar(
            self.root,
            mode='indeterminate',
            length=700
        )
        self.progress.pack(pady=5)

        # Поле вывода логов
        log_frame = tk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(
            log_frame,
            text="Лог операций:",
            font=("Arial", 10, "bold"),
            anchor="w"
        ).pack(anchor="w")

        self.output_area = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=90,
            height=15,
            font=("Consolas", 9)
        )
        self.output_area.pack(fill=tk.BOTH, expand=True)

        # Нижний фрейм со статистикой
        stats_frame = tk.Frame(self.root)
        stats_frame.pack(fill=tk.X, padx=20, pady=5)

        self.label_stats = tk.Label(
            stats_frame,
            text="",
            font=("Arial", 9),
            fg="blue",
            anchor="w"
        )
        self.label_stats.pack(side=tk.LEFT)

    def select_folder(self):
        """Обработчик выбора папки."""
        folder = filedialog.askdirectory(title="Выберите папку с фото и видео")

        if folder:
            self.folder_path = folder
            self.label_selected.config(
                text=f"✅ Выбрана папка: {folder}",
                fg="green"
            )
            self.btn_run.config(state=tk.NORMAL)
            self.log_message(f"📁 Выбрана папка: {folder}\n")

    def log_message(self, message: str):
        """Добавить сообщение в лог."""
        self.output_area.insert(tk.END, message + "\n")
        self.output_area.see(tk.END)
        self.root.update_idletasks()

    def update_stats(self, stats: dict):
        """Обновить статистику."""
        text = (
            f"Обработано: {stats['total']} | "
            f"✅ Успешно: {stats['success']} | "
            f"⏩ Пропущено: {stats['skipped']} | "
            f"❌ Ошибок: {stats['errors']}"
        )
        self.label_stats.config(text=text)
    
    def show_renamed_dialog(self, renamed_files: List[Path], to_rename_count: int):
        """
        Показать диалог с уже переименованными файлами.
        
        Args:
            renamed_files: список уже переименованных файлов
            to_rename_count: количество файлов, требующих переименования
        """
        dialog = RenamedFilesDialog(self.root, renamed_files, to_rename_count)
        self.root.wait_window(dialog)
        
        # Получаем результат и отправляем в очередь
        result = dialog.get_result()
        if result is None:
            result = "cancel"
        self.choice_queue.put(result)

    def start_processing(self):
        """Запустить обработку файлов."""
        if not self.folder_path:
            messagebox.showwarning("Ошибка", "Сначала выберите папку!")
            return

        if self.is_processing:
            messagebox.showinfo("Информация", "Обработка уже выполняется!")
            return

        # Очищаем лог
        self.output_area.delete(1.0, tk.END)
        self.label_stats.config(text="")

        # Подтверждение в реальном режиме
        if not self.dry_run.get():
            result = messagebox.askyesno(
                "Подтверждение",
                "⚠️ Вы уверены?\n\n"
                "Будет выполнено РЕАЛЬНОЕ переименование файлов!\n"
                "Рекомендуется сделать резервную копию.\n\n"
                "Продолжить?",
                icon='warning'
            )
            if not result:
                return

        # Информация о режиме
        mode = "ТЕСТОВЫЙ РЕЖИМ" if self.dry_run.get() else "РЕАЛЬНОЕ ПЕРЕИМЕНОВАНИЕ"
        self.log_message(f"🚀 Начинаем обработку в режиме: {mode}")
        self.log_message(f"📁 Папка: {self.folder_path}")
        self.log_message("-" * 80)

        # Блокируем кнопки
        self.btn_select.config(state=tk.DISABLED)
        self.btn_run.config(state=tk.DISABLED)
        self.check_test.config(state=tk.DISABLED)
        self.check_folders.config(state=tk.DISABLED)

        # Запускаем прогресс
        self.progress.start(10)

        # Запускаем обработку в отдельном потоке
        self.is_processing = True
        thread = threading.Thread(target=self.process_files_thread, daemon=True)
        thread.start()

    def process_files_thread(self):
        """Обработка файлов в отдельном потоке."""
        try:
            stats = {
                'total': 0,
                'success': 0,
                'skipped': 0,
                'errors': 0
            }

            # Инициализация инструментов v1.3
            template_parser = TemplateParser(self.template_str.get())
            folder_organizer = FolderOrganizer() if self.organize_folders.get() else None
            
            if folder_organizer:
                self.log_message("📁 Группировка по папкам ВКЛЮЧЕНА")
            
            self.log_message(f"📝 Используемый шаблон: {self.template_str.get()}\n")

            root = Path(self.folder_path)
            supported_exts = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS

            # Сначала собираем все файлы и разделяем на уже переименованные и новые
            all_files = [
                f for f in root.rglob('*')
                if f.is_file() and f.suffix.lower() in supported_exts
            ]
            
            already_renamed = []
            to_rename = []
            
            for file_path in all_files:
                is_renamed, _ = is_already_renamed(file_path.name)
                if is_renamed:
                    already_renamed.append(file_path)
                else:
                    to_rename.append(file_path)
            
            self.log_message(f"📊 Найдено файлов: {len(all_files)}")
            self.log_message(f"   • Уже переименованных: {len(already_renamed)}")
            self.log_message(f"   • Требуют переименования: {len(to_rename)}\n")
            
            # Если найдены уже переименованные файлы, показываем диалог
            files_to_process = to_rename
            
            if already_renamed:
                self.log_message("⚠️ Обнаружены уже переименованные файлы. Ожидание выбора пользователя...\n")
                
                # Показываем диалог в главном потоке
                self.root.after(0, lambda: self.show_renamed_dialog(already_renamed, len(to_rename)))
                
                # Ожидаем ответ пользователя
                user_choice = self.choice_queue.get()
                
                if user_choice == "cancel":
                    self.log_message("❌ Операция отменена пользователем\n")
                    return
                elif user_choice == "skip":
                    self.log_message(f"⏩ Пропускаем {len(already_renamed)} уже переименованных файлов\n")
                    self.log_message(f"📊 Будет обработано: {len(to_rename)} файлов\n")
                    files_to_process = to_rename
                elif user_choice == "rerename":
                    self.log_message(f"🔄 Переименовываем заново все файлы\n")
                    self.log_message(f"📊 Будет обработано: {len(all_files)} файлов\n")
                    files_to_process = all_files
            
            self.log_message("-" * 80 + "\n")

            # Обрабатываем файлы
            for file_path in files_to_process:
                stats['total'] += 1

                success, message = process_file(
                    str(file_path), 
                    self.dry_run.get(),
                    template_parser,
                    folder_organizer
                )

                if success:
                    stats['success'] += 1
                elif 'Пропущен' in message or 'Уже переименован' in message:
                    stats['skipped'] += 1
                else:
                    stats['errors'] += 1

                self.log_message(message)
                self.update_stats(stats)

            # Итоговая статистика
            self.log_message("\n" + "-" * 80)
            self.log_message("✅ ОБРАБОТКА ЗАВЕРШЕНА!")
            self.log_message(f"   Всего файлов: {stats['total']}")
            self.log_message(f"   ✅ Успешно: {stats['success']}")
            self.log_message(f"   ⏩ Пропущено: {stats['skipped']}")
            self.log_message(f"   ❌ Ошибок: {stats['errors']}")

            if self.dry_run.get():
                self.log_message("\n💡 Снимите галочку 'Тестовый режим' для реального переименования")

            # Показываем финальное сообщение
            self.root.after(0, lambda: self.show_completion_message(stats))

        except Exception as e:
            self.log_message(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Произошла ошибка:\n{e}"))

        finally:
            # Останавливаем прогресс и разблокируем кнопки
            self.root.after(0, self.finish_processing)

    def show_completion_message(self, stats: dict):
        """Показать сообщение о завершении."""
        if self.dry_run.get():
            messagebox.showinfo(
                "Тест завершён",
                f"Тестовый режим завершён!\n\n"
                f"Файлов обработано: {stats['total']}\n"
                f"Будет переименовано: {stats['success']}\n\n"
                f"Снимите галочку 'Тестовый режим' для реального переименования."
            )
        else:
            messagebox.showinfo(
                "Готово!",
                f"Переименование завершено!\n\n"
                f"Всего файлов: {stats['total']}\n"
                f"✅ Успешно: {stats['success']}\n"
                f"⏩ Пропущено: {stats['skipped']}\n"
                f"❌ Ошибок: {stats['errors']}"
            )

    def finish_processing(self):
        """Завершить обработку: остановить прогресс и разблокировать кнопки."""
        self.progress.stop()
        self.btn_select.config(state=tk.NORMAL)
        self.btn_run.config(state=tk.NORMAL)
        self.check_test.config(state=tk.NORMAL)
        self.check_folders.config(state=tk.NORMAL)
        self.is_processing = False


# =============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# =============================================================================

def main():
    """Главная функция: запуск GUI приложения."""
    root = tk.Tk()

    # Устанавливаем иконку (если есть)
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass

    app = RenameMediaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
