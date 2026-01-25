#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки функции is_already_renamed()
"""

import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from rename_media_gui import is_already_renamed, RENAMED_PATTERN

def test_is_already_renamed():
    """Тестирование функции is_already_renamed()"""
    
    test_cases = [
        ("Photo-2023-08-15_142203.jpg", True, "Photo"),
        ("Video-2024-01-10_091530.mp4", True, "Video"),
        ("Photo-2023-08-15_142203_1.jpg", True, "Photo"),
        ("Photo-2023-08-15_142203_99.png", True, "Photo"),
        ("video-2020-01-01_000000.avi", True, "video"),  # case insensitive
        ("IMG_20230815.jpg", False, ""),
        ("VID_20240110.mp4", False, ""),
        ("my_photo.jpg", False, ""),
        ("Photo-2023-08-15.jpg", False, ""),  # нет времени
        ("Photo-23-08-15_142203.jpg", False, ""),  # неправильный год
    ]
    
    print("=" * 70)
    print("Тестирование функции is_already_renamed()")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    
    for filename, expected_match, expected_prefix in test_cases:
        is_match, prefix = is_already_renamed(filename)
        
        if is_match == expected_match and prefix == expected_prefix:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status} | {filename:40} | Match: {is_match:5} | Prefix: '{prefix}'")
        if is_match != expected_match or prefix != expected_prefix:
            print(f"       Expected: Match: {expected_match:5} | Prefix: '{expected_prefix}'")
    
    print()
    print("=" * 70)
    print(f"Результаты: {passed} пройдено, {failed} провалено")
    print("=" * 70)
    
    return failed == 0

if __name__ == "__main__":
    success = test_is_already_renamed()
    sys.exit(0 if success else 1)
