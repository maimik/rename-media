#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер истории операций для поддержки функции Undo.
Версия: 1.0
Автор: Claude Sonnet 4.5
Дата: 2026-01-27
"""

import json
import os
import sys
import ctypes
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

class HistoryManager:
    """Управление журналом изменений и отмена операций."""

    HISTORY_FILENAME = ".rename_history.json"
    MAX_HISTORY_SIZE = 10

    def __init__(self, base_dir: Path):
        """
        Инициализация менеджера истории.
        
        Args:
            base_dir: Папка, в которой выполняется переименование и где хранится история.
        """
        self.base_dir = Path(base_dir)
        self.history_file = self.base_dir / self.HISTORY_FILENAME
        self.history: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        """Загрузить историю из файла."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, IOError) as e:
            print(f"[!] Ошибка чтения файла истории: {e}. Будет создан новый.")
            return []

    def _save(self) -> None:
        """Сохранить историю в файл."""
        try:
            # Снять атрибут "скрытый" перед записью (Windows)
            if os.name == 'nt' and self.history_file.exists():
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(str(self.history_file), 0)
                except Exception:
                    pass

            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            
            # Установить атрибут "скрытый" после записи (Windows)
            if os.name == 'nt':
                try:
                    FILE_ATTRIBUTE_HIDDEN = 0x02
                    ctypes.windll.kernel32.SetFileAttributesW(
                        str(self.history_file), FILE_ATTRIBUTE_HIDDEN
                    )
                except Exception:
                    pass  # Не критично, если не удалось скрыть
        except IOError as e:
            print(f"[X] Ошибка сохранения истории: {e}")

    def record(self, files_mapping: List[Dict[str, str]], operation: str = "rename") -> None:
        """
        Записать операцию в историю.

        Args:
            files_mapping: Список изменений [{'old': 'old_rel_path', 'new': 'new_rel_path'}]
            operation: Тип операции (по умолчанию "rename")
        """
        if not files_mapping:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "files": files_mapping
        }

        # Добавляем в начало списка
        self.history.insert(0, entry)

        # Обрезаем до лимита
        if len(self.history) > self.MAX_HISTORY_SIZE:
            self.history = self.history[:self.MAX_HISTORY_SIZE]

        self._save()

    def get_history(self) -> List[Dict[str, Any]]:
        """Получить список операций."""
        return self.history

    def clear(self) -> None:
        """Очистить всю историю."""
        self.history = []
        if self.history_file.exists():
            try:
                os.remove(self.history_file)
            except OSError as e:
                print(f"[X] Ошибка удаления файла истории: {e}")

    def undo(self) -> Tuple[bool, List[str], List[str]]:
        """
        Отменить последнюю операцию.

        Returns:
            Tuple[bool, success_messages, error_messages]:
                - Успех операции (полный или частичный)
                - Список сообщений об успехе
                - Список ошибок
        """
        if not self.history:
            return False, [], ["История пуста, нечего отменять."]

        last_operation = self.history[0]
        files = last_operation.get("files", [])
        
        success_msgs = []
        error_msgs = []
        files_processed = 0

        # Обрабатываем файлы в обратном порядке (на случай зависимостей)
        # Хотя для переименования это обычно не критично, но хорошая практика
        for item in reversed(files):
            old_rel_path = item.get("old")
            new_rel_path = item.get("new")

            if not old_rel_path or not new_rel_path:
                continue

            current_path = self.base_dir / new_rel_path
            original_path = self.base_dir / old_rel_path

            if not current_path.exists():
                error_msgs.append(f"Файл не найден (удален или перемещен): {new_rel_path}")
                continue

            if original_path.exists():
                error_msgs.append(f"Целевой файл уже существует: {old_rel_path}")
                continue

            try:
                # Если файл был перемещен в подпапку, а мы возвращаем его в корень,
                # папка назначения (корень) скорее всего существует.
                # Но если "old" путь тоже был в подпапке, надо проверить её создание.
                if not original_path.parent.exists():
                    original_path.parent.mkdir(parents=True, exist_ok=True)

                os.rename(current_path, original_path)
                success_msgs.append(f"Откат: {new_rel_path} -> {old_rel_path}")
                files_processed += 1
                
                # Попытка удалить пустую папку, если файл был единственным в ней
                # (актуально при "Группировке по папкам")
                if current_path.parent != self.base_dir:
                    try:
                        current_path.parent.rmdir()  # Удалит только если пустая
                    except OSError:
                        pass # Папка не пуста, это нормально

            except OSError as e:
                error_msgs.append(f"Ошибка переименования {new_rel_path}: {e}")

        # Удаляем операцию из истории, только если хоть что-то попытались сделать
        # или если операция была фактически пустой или невыполнимой, 
        # чтобы пользователь не застрял на ней.
        # В данном случае, удаляем, так как попытка отката совершена.
        self.history.pop(0)
        self._save()

        return files_processed > 0, success_msgs, error_msgs

if __name__ == "__main__":
    # Тестирование модуля
    print("=== Тестирование HistoryManager ===")
    
    test_dir = Path("test_history_zone")
    test_dir.mkdir(exist_ok=True)
    
    manager = HistoryManager(test_dir)
    manager.clear() # Начинаем с чистого листа
    
    # Создаем фиктивные файлы для теста
    file1 = test_dir / "test1.txt"
    file2 = test_dir / "test2.txt"
    
    with open(file1, 'w') as f: f.write("content1")
    with open(file2, 'w') as f: f.write("content2")
    
    print(f"1. Созданы файлы: {file1}, {file2}")
    
    # 2. Симуляция переименования
    new_file1 = test_dir / "renamed1.txt"
    new_file2 = test_dir / "subfolder" / "renamed2.txt"
    
    new_file2.parent.mkdir(exist_ok=True)
    
    os.rename(file1, new_file1)
    os.rename(file2, new_file2)
    
    print(f"2. Файлы переименованы в: {new_file1.name}, {new_file2.relative_to(test_dir)}")
    
    # 3. Запись в историю
    record_data = [
        {"old": "test1.txt", "new": "renamed1.txt"},
        {"old": "test2.txt", "new": str(Path("subfolder") / "renamed2.txt")}
    ]
    manager.record(record_data)
    print("3. Операция записана в историю.")
    
    # Проверка скрытости файла (только визуально или через атрибуты)
    hist_file = test_dir / ".rename_history.json"
    if hist_file.exists():
        print(f"4. Файл истории создан: {hist_file}")
    
    # 4. Откат
    print("5. Выполняем Undo...")
    success, msgs, errs = manager.undo()
    
    for msg in msgs:
        print(f"   [OK] {msg}")
    for err in errs:
        print(f"   [ERR] {err}")
        
    # Проверка результата
    if file1.exists() and file2.exists():
        print("6. УСПЕХ: Файлы вернулись на свои места.")
    else:
        print("6. ОШИБКА: Файлы не восстановлены полностью.")
        
    # Очистка
    try:
        os.remove(file1)
        os.remove(file2)
        if new_file2.parent.exists():
             new_file2.parent.rmdir()
        test_dir.rmdir()
        if hist_file.exists(): # Should be gone after undo? No, undo removes entry, clear removes file
            pass
        manager.clear() # Clean up file
        test_dir.rmdir() # Try remove dir again if not empty
    except Exception as e:
        print(f"Очистка теста: {e}")
    
    print("Тест завершен.")
