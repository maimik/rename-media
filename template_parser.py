#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер шаблонов для форматирования имён файлов.
Версия: 1.2
Автор: Claude Sonnet 4.5
Дата: 2026-01-25
"""

import re
from datetime import datetime
from typing import Dict, Callable


class TemplateParser:
    """Парсер шаблонов имён файлов с поддержкой переменных."""
    
    # Словарь поддерживаемых переменных и их обработчиков
    VARIABLES: Dict[str, Callable[[datetime, str], str]] = {
        'type': lambda d, t: t,  # Photo/Video
        'YYYY': lambda d, t: d.strftime('%Y'),  # Год (4 цифры)
        'YY': lambda d, t: d.strftime('%y'),    # Год (2 цифры)
        'MM': lambda d, t: d.strftime('%m'),    # Месяц
        'DD': lambda d, t: d.strftime('%d'),    # День
        'HH': lambda d, t: d.strftime('%H'),    # Час (24ч)
        'hh': lambda d, t: d.strftime('%I'),    # Час (12ч)
        'mm': lambda d, t: d.strftime('%M'),    # Минуты
        'ss': lambda d, t: d.strftime('%S'),    # Секунды
        'HHmmss': lambda d, t: d.strftime('%H%M%S'),  # Время слитно
    }
    
    # Шаблон по умолчанию (текущий формат)
    DEFAULT_TEMPLATE = "{type}-{YYYY}-{MM}-{DD}_{HHmmss}"
    
    def __init__(self, template: str = None):
        """
        Инициализация парсера шаблонов.
        
        Args:
            template: шаблон имени файла (если None, используется DEFAULT_TEMPLATE)
        
        Raises:
            ValueError: если шаблон содержит неизвестные переменные
        """
        self.template = template or self.DEFAULT_TEMPLATE
        self.validate()
    
    def validate(self) -> None:
        """
        Проверить корректность шаблона.
        
        Raises:
            ValueError: если шаблон содержит неизвестные переменные
        """
        # Находим все переменные в шаблоне
        pattern = r'\{(\w+)\}'
        variables = re.findall(pattern, self.template)
        
        # Проверяем каждую переменную
        unknown_vars = []
        for var in variables:
            if var not in self.VARIABLES:
                unknown_vars.append(var)
        
        if unknown_vars:
            raise ValueError(
                f"Неизвестные переменные в шаблоне: {', '.join(f'{{{v}}}' for v in unknown_vars)}\n"
                f"Доступные переменные: {', '.join(f'{{{v}}}' for v in self.VARIABLES.keys())}"
            )
    
    def format(self, date: datetime, file_type: str) -> str:
        """
        Сформировать имя файла по шаблону.
        
        Args:
            date: дата для форматирования
            file_type: тип файла ("Photo" или "Video")
        
        Returns:
            отформатированное имя файла (без расширения)
        
        Examples:
            >>> parser = TemplateParser("{type}-{YYYY}-{MM}-{DD}_{HHmmss}")
            >>> parser.format(datetime(2023, 8, 15, 14, 22, 3), "Photo")
            'Photo-2023-08-15_142203'
            
            >>> parser = TemplateParser("IMG_{YYYY}{MM}{DD}_{HHmmss}")
            >>> parser.format(datetime(2023, 8, 15, 14, 22, 3), "Photo")
            'IMG_20230815_142203'
        """
        result = self.template
        
        # Заменяем каждую переменную её значением
        for var, func in self.VARIABLES.items():
            placeholder = f"{{{var}}}"
            if placeholder in result:
                value = func(date, file_type)
                result = result.replace(placeholder, value)
        
        return result
    
    @classmethod
    def get_help_text(cls) -> str:
        """
        Получить справку по доступным переменным.
        
        Returns:
            текст справки
        """
        help_lines = [
            "Доступные переменные для шаблонов:",
            "",
            "  {type}    - Photo или Video",
            "  {YYYY}    - Год (4 цифры), например: 2024",
            "  {YY}      - Год (2 цифры), например: 24",
            "  {MM}      - Месяц (2 цифры), например: 08",
            "  {DD}      - День (2 цифры), например: 15",
            "  {HH}      - Час в 24ч формате, например: 14",
            "  {hh}      - Час в 12ч формате, например: 02",
            "  {mm}      - Минуты, например: 22",
            "  {ss}      - Секунды, например: 03",
            "  {HHmmss}  - Время слитно, например: 142203",
            "",
            "Примеры шаблонов:",
            "",
            "  {type}-{YYYY}-{MM}-{DD}_{HHmmss}",
            "    → Photo-2023-08-15_142203.jpg",
            "",
            "  IMG_{YYYY}{MM}{DD}_{HHmmss}",
            "    → IMG_20230815_142203.jpg",
            "",
            "  {type}_{DD}.{MM}.{YYYY}_{HH}-{mm}-{ss}",
            "    → Photo_15.08.2023_14-22-03.jpg",
            "",
            "  {YYYY}/{MM}/{type}_{YYYY}{MM}{DD}",
            "    → 2023/08/Photo_20230815.jpg",
        ]
        return "\n".join(help_lines)


if __name__ == "__main__":
    # Примеры использования
    print("=== Тестирование TemplateParser ===\n")
    
    test_date = datetime(2023, 8, 15, 14, 22, 3)
    
    templates = [
        "{type}-{YYYY}-{MM}-{DD}_{HHmmss}",
        "IMG_{YYYY}{MM}{DD}_{HHmmss}",
        "{type}_{DD}.{MM}.{YYYY}_{HH}-{mm}-{ss}",
        "{YYYY}/{MM}/{type}_{YYYY}{MM}{DD}",
    ]
    
    for template in templates:
        parser = TemplateParser(template)
        result = parser.format(test_date, "Photo")
        print(f"Шаблон: {template}")
        print(f"Результат: {result}")
        print()
    
    # Тест валидации
    print("=== Тест валидации ===\n")
    try:
        invalid_parser = TemplateParser("{type}-{INVALID}-{YYYY}")
    except ValueError as e:
        print(f"Ожидаемая ошибка: {e}")
    
    print("\n=== Справка ===\n")
    print(TemplateParser.get_help_text())
