"""
Главный контроллер приложения
Координирует работу всех модулей
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, Dict
import logging

from src.database.connection import DatabaseConnection
from src.database.models import DatabaseModels
from src.services.auth import AuthService
from src.services.sales import SalesService
from src.services.reports import ReportsService
from src.services.backup import BackupService
from src.utils.config import ConfigManager
from src.utils.logger import setup_logging
from src.ui.login_window import LoginWindow
from src.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class StroyUchetApp:
    """Главный класс приложения"""
    
    def __init__(self, base_dir: Optional[Path] = None, 
                 data_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.cwd()
        self.data_dir = data_dir or self.base_dir / 'data'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка логирования
        setup_logging(self.data_dir / 'logs')
        
        # Инициализация конфигурации
        self.config = ConfigManager(self.data_dir / 'config.ini')
        
        # Инициализация базы данных
        self.db_path = self.data_dir / 'database.db'
        self.db = DatabaseConnection(self.db_path)
        self.models = DatabaseModels(self.db)
        
        # Создание таблиц если их нет
        self._init_database()
        
        # Инициализация сервисов
        self._init_services()
        
        # Текущий пользователь
        self.current_user: Optional[Dict] = None
        
        # Главное окно
        self.main_window: Optional[MainWindow] = None
        
        # Настройка темы CustomTkinter
        self._setup_theme()
    
    def _init_database(self):
        """Инициализация структуры базы данных"""
        tables = self.db.get_table_names()
        
        if not tables or 'users' not in tables:
            logger.info("Создание структуры базы данных...")
            self.models.create_all_tables()
    
    def _init_services(self):
        """Инициализация сервисов после создания БД"""
        self.auth_service = AuthService(self.db)
        self.sales_service = SalesService(self.db)
        self.reports_service = ReportsService(self.db, self.data_dir / 'exports')
        self.backup_service = BackupService(self.db_path, self.data_dir / 'backups')
        
        # Создание пользователя по умолчанию если БД пустая
        self._create_default_user()
    
    def _create_default_user(self):
        """Создание пользователя admin по умолчанию"""
        result = self.auth_service.create_user(
            username='admin',
            password='admin123',
            full_name='Администратор',
            role='admin'
        )
        
        if result['success']:
            logger.info("Создан пользователь по умолчанию: admin / admin123")
    
    def _setup_theme(self):
        """Настройка темы интерфейса"""
        theme = self.config.get('app', 'theme', 'system')
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme('blue')
    
    def run(self):
        """Запуск приложения"""
        self.root = ctk.CTk()
        self.root.withdraw()  # Скрыть корневое окно
        
        # Показать окно авторизации
        self.show_login()
        
        # Запуск главного цикла
        self.root.mainloop()
        
        # Закрытие соединения с БД
        self.db.close()
        
        # Создание бэкапа при закрытии
        if self.config.get_bool('database', 'auto_backup', True):
            self.backup_service.schedule_daily_backup()
    
    def show_login(self):
        """Показ окна авторизации"""
        login_window = LoginWindow(self, master=self.root)
        login_window.transient(self.root)
        login_window.grab_set()
    
    def show_main(self, user: Dict):
        """Показ главного окна после авторизации"""
        self.current_user = user
        
        if self.main_window is None or not self.main_window.winfo_exists():
            self.main_window = MainWindow(self, master=self.root)
            self.main_window.deiconify()
            self.main_window.set_user(user)
        else:
            self.main_window.deiconify()
            self.main_window.set_user(user)
    
    def authenticate(self, username: str, password: str) -> Dict:
        """
        Аутентификация пользователя (вызывается из LoginWindow)
        
        Args:
            username: Имя пользователя
            password: Пароль
            
        Returns:
            Dict с результатом аутентификации
        """
        return self.auth_service.authenticate(username, password)


def main():
    """Точка входа в приложение"""
    import sys
    
    # Определение путей для packaged-версии
    if getattr(sys, 'frozen', False):
        # Запущен как EXE
        from pathlib import Path
        import os
        BASE_DIR = Path(sys._MEIPASS)
        APP_DATA = Path(os.getenv('APPDATA')) / 'StroyUchet'
    else:
        # Запущен как скрипт
        BASE_DIR = Path(__file__).parent.parent
        APP_DATA = BASE_DIR / 'data'
    
    APP_DATA.mkdir(parents=True, exist_ok=True)
    
    app = StroyUchetApp(base_dir=BASE_DIR, data_dir=APP_DATA)
    app.run()


if __name__ == "__main__":
    main()
