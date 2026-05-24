"""
Точка входа в приложение СтройУчёт
"""

import sys
from pathlib import Path

# Добавление корневой директории в path
if getattr(sys, 'frozen', False):
    # Запущен как EXE
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Запущен как скрипт
    BASE_DIR = Path(__file__).parent

sys.path.insert(0, str(BASE_DIR))


def main():
    """Основная функция запуска"""
    from src.app import StroyUchetApp
    
    # Определение директории для данных
    if getattr(sys, 'frozen', False):
        import os
        APP_DATA = Path(os.getenv('APPDATA')) / 'StroyUchet'
    else:
        APP_DATA = BASE_DIR / 'data'
    
    APP_DATA.mkdir(parents=True, exist_ok=True)
    
    # Создание и запуск приложения
    app = StroyUchetApp(base_dir=BASE_DIR, data_dir=APP_DATA)
    app.run()


if __name__ == "__main__":
    main()
