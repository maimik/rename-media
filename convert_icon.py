#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для конвертации PNG иконки в ICO формат для использования в EXE
"""

from PIL import Image
import sys

def convert_png_to_ico(png_path, ico_path):
    """
    Конвертировать PNG в ICO формат.

    Args:
        png_path: путь к PNG файлу
        ico_path: путь для сохранения ICO файла
    """
    # Устанавливаем UTF-8 для Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    try:
        # Открываем PNG изображение
        img = Image.open(png_path)

        # Создаём несколько размеров для ICO (стандартные размеры для Windows)
        sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

        # Конвертируем в RGBA если нужно
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Сохраняем как ICO с несколькими размерами
        img.save(ico_path, format='ICO', sizes=sizes)

        print("[OK] Иконка успешно конвертирована!")
        print(f"     Из: {png_path}")
        print(f"     В:  {ico_path}")
        print(f"     Размеры: {', '.join([f'{w}x{h}' for w, h in sizes])}")
        return True

    except Exception as e:
        print(f"[X] Ошибка конвертации: {e}")
        return False


if __name__ == "__main__":
    # Устанавливаем UTF-8 для Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    png_file = "Robsonbillponte-Sinem-File-Picture.512.png"
    ico_file = "app_icon.ico"

    print("=" * 70)
    print("  Конвертация PNG в ICO для использования в EXE")
    print("=" * 70)
    print()

    if convert_png_to_ico(png_file, ico_file):
        print()
        print("[OK] Готово! Теперь можно использовать app_icon.ico при создании EXE:")
        print()
        print("   pyinstaller --onefile --windowed \\")
        print("               --icon=app_icon.ico \\")
        print("               --name='RenameMedia' \\")
        print("               rename_media_gui.py")
        sys.exit(0)
    else:
        sys.exit(1)
