#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки логики сканирования файлов
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from rename_media_gui import is_already_renamed, PHOTO_EXTENSIONS, VIDEO_EXTENSIONS

def test_scan_logic():
    """Тестирование логики сканирования файлов"""
    
    print("=" * 70)
    print("Тестирование логики сканирования файлов в папке Files/")
    print("=" * 70)
    print()
    
    root = Path("Files")
    supported_exts = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS
    
    # Собираем все файлы
    all_files = [
        f for f in root.rglob('*')
        if f.is_file() and f.suffix.lower() in supported_exts
    ]
    
    already_renamed = []
    to_rename = []
    
    for file_path in all_files:
        is_renamed, prefix = is_already_renamed(file_path.name)
        if is_renamed:
            already_renamed.append(file_path)
        else:
            to_rename.append(file_path)
    
    print(f"📊 Всего файлов: {len(all_files)}")
    print(f"   • Уже переименованных: {len(already_renamed)}")
    print(f"   • Требуют переименования: {len(to_rename)}")
    print()
    
    if already_renamed:
        print("✅ Уже переименованные файлы:")
        for file_path in already_renamed[:10]:  # Показываем первые 10
            is_renamed, prefix = is_already_renamed(file_path.name)
            icon = "📷" if prefix.lower() == "photo" else "🎬"
            print(f"   {icon} {file_path.name}")
        if len(already_renamed) > 10:
            print(f"   ... и ещё {len(already_renamed) - 10} файлов")
        print()
    
    if to_rename:
        print("📝 Требуют переименования (примеры):")
        for file_path in to_rename[:10]:  # Показываем первые 10
            ext = file_path.suffix.lower()
            icon = "📷" if ext in PHOTO_EXTENSIONS else "🎬"
            print(f"   {icon} {file_path.name}")
        if len(to_rename) > 10:
            print(f"   ... и ещё {len(to_rename) - 10} файлов")
        print()
    
    print("=" * 70)
    print("✅ Тест завершён успешно!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = test_scan_logic()
    sys.exit(0 if success else 1)
