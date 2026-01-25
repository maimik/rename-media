#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Организатор файлов по папкам на основе дат.
Версия: 1.2
Автор: Claude Sonnet 4.5
Дата: 2026-01-25
"""

from datetime import datetime
from pathlib import Path
from typing import Literal


# Типы структур папок
FolderStructure = Literal['none', 'year', 'year-month', 'date']


class FolderOrganizer:
    """Организация файлов по папкам на основе дат."""
    
    def __init__(self, structure: FolderStructure = 'none'):
        """
        Инициализация организатора папок.
        
        Args:
            structure: тип структуры папок
                - 'none': без организации (все файлы в одной папке)
                - 'year': группировка по годам (2023/, 2024/)
                - 'year-month': группировка по годам и месяцам (2023/08/, 2024/01/)
                - 'date': группировка по датам (2023-08-15/, 2024-01-10/)
        
        Raises:
            ValueError: если указана неизвестная структура
        """
        valid_structures = ['none', 'year', 'year-month', 'date']
        if structure not in valid_structures:
            raise ValueError(
                f"Неизвестная структура: '{structure}'\n"
                f"Доступные структуры: {', '.join(valid_structures)}"
            )
        
        self.structure = structure
    
    def get_folder_path(self, base_dir: Path, date: datetime) -> Path:
        """
        Получить путь к папке для файла на основе даты.
        
        Args:
            base_dir: базовая директория
            date: дата файла
        
        Returns:
            полный путь к папке
        
        Examples:
            >>> organizer = FolderOrganizer('year')
            >>> organizer.get_folder_path(Path('/photos'), datetime(2023, 8, 15))
            Path('/photos/2023')
            
            >>> organizer = FolderOrganizer('year-month')
            >>> organizer.get_folder_path(Path('/photos'), datetime(2023, 8, 15))
            Path('/photos/2023/08')
            
            >>> organizer = FolderOrganizer('date')
            >>> organizer.get_folder_path(Path('/photos'), datetime(2023, 8, 15))
            Path('/photos/2023-08-15')
        """
        if self.structure == 'none':
            return base_dir
        elif self.structure == 'year':
            return base_dir / date.strftime('%Y')
        elif self.structure == 'year-month':
            return base_dir / date.strftime('%Y') / date.strftime('%m')
        elif self.structure == 'date':
            return base_dir / date.strftime('%Y-%m-%d')
        else:
            # Не должно произойти из-за валидации в __init__
            raise ValueError(f"Неизвестная структура: {self.structure}")
    
    def create_folder(self, folder_path: Path, dry_run: bool = False) -> bool:
        """
        Создать папку если её нет.
        
        Args:
            folder_path: путь к папке
            dry_run: если True, не создавать папку реально
        
        Returns:
            True если папка была создана, False если уже существовала
        """
        if folder_path.exists():
            return False
        
        if not dry_run:
            folder_path.mkdir(parents=True, exist_ok=True)
        
        return True
    
    def get_description(self) -> str:
        """
        Получить описание текущей структуры.
        
        Returns:
            текстовое описание структуры
        """
        descriptions = {
            'none': 'Без организации (все файлы в одной папке)',
            'year': 'По годам (2023/, 2024/)',
            'year-month': 'По годам и месяцам (2023/08/, 2024/01/)',
            'date': 'По датам (2023-08-15/, 2024-01-10/)',
        }
        return descriptions.get(self.structure, 'Неизвестная структура')
    
    @staticmethod
    def get_help_text() -> str:
        """
        Получить справку по доступным структурам.
        
        Returns:
            текст справки
        """
        help_lines = [
            "Доступные структуры организации файлов:",
            "",
            "  none        - Без организации",
            "                Все файлы остаются в исходной папке",
            "",
            "  year        - По годам",
            "                Структура: 2023/, 2024/",
            "                Пример: 2023/Photo-2023-08-15_142203.jpg",
            "",
            "  year-month  - По годам и месяцам",
            "                Структура: 2023/08/, 2024/01/",
            "                Пример: 2023/08/Photo-2023-08-15_142203.jpg",
            "",
            "  date        - По датам",
            "                Структура: 2023-08-15/, 2024-01-10/",
            "                Пример: 2023-08-15/Photo-2023-08-15_142203.jpg",
        ]
        return "\n".join(help_lines)


if __name__ == "__main__":
    # Примеры использования
    print("=== Тестирование FolderOrganizer ===\n")
    
    test_date = datetime(2023, 8, 15, 14, 22, 3)
    base_dir = Path("/photos")
    
    structures = ['none', 'year', 'year-month', 'date']
    
    for structure in structures:
        organizer = FolderOrganizer(structure)
        folder_path = organizer.get_folder_path(base_dir, test_date)
        print(f"Структура: {structure}")
        print(f"Описание: {organizer.get_description()}")
        print(f"Путь: {folder_path}")
        print()
    
    # Тест валидации
    print("=== Тест валидации ===\n")
    try:
        invalid_organizer = FolderOrganizer('invalid')
    except ValueError as e:
        print(f"Ожидаемая ошибка: {e}")
    
    print("\n=== Справка ===\n")
    print(FolderOrganizer.get_help_text())
