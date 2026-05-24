"""
Модуль главного окна приложения
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, Callable
import logging

from .products_frame import ProductsFrame

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTkToplevel):
    """Главное окно приложения (как диалоговое окно)"""
    
    def __init__(self, app_controller, **kwargs):
        # Извлекаем master из kwargs, чтобы избежать дублирования аргументов
        master = kwargs.pop('master', None) or app_controller.root
        
        super().__init__(master=master, **kwargs)
        
        self.app_controller = app_controller
        self.current_user = None
        
        # Настройка окна
        self.title("СтройУчёт v1.0.0")
        self.geometry("1280x720")
        self.minsize(1024, 600)
        
        # Настройка сетки
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Создание интерфейса
        self._create_sidebar()
        self._create_header()
        self._create_main_area()
        self._create_statusbar()
        
        # Привязка горячих клавиш
        self._bind_hotkeys()
    
    def _create_sidebar(self):
        """Создание боковой панели навигации"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        
        # Логотип
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="🏗️ СтройУчёт",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Кнопки навигации
        nav_buttons = [
            ("📊 Панель", self._on_dashboard),
            ("📦 Товары", self._on_products),
            ("👥 Клиенты", self._on_customers),
            ("💰 Продажи", self._on_sales),
            ("📥 Склад", self._on_warehouse),
            ("📈 Отчёты", self._on_reports),
            ("⚙ Настройки", self._on_settings),
        ]
        
        for i, (text, command) in enumerate(nav_buttons, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                anchor="w"
            )
            btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
        
        # Кнопка выхода
        self.logout_btn = ctk.CTkButton(
            self.sidebar,
            text="🚪 Выход",
            command=self._on_logout,
            fg_color="#DC3545",
            hover_color="#C82333"
        )
        self.logout_btn.grid(row=9, column=0, padx=10, pady=(10, 20), sticky="ew")
    
    def _create_header(self):
        """Создание заголовка"""
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header.grid(row=0, column=1, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)
        
        # Название раздела
        self.section_title = ctk.CTkLabel(
            self.header,
            text="Панель управления",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.section_title.grid(row=0, column=0, padx=20, sticky="w")
        
        # Информация о пользователе
        self.user_info = ctk.CTkLabel(
            self.header,
            text="Пользователь",
            font=ctk.CTkFont(size=14)
        )
        self.user_info.grid(row=0, column=1, padx=20, sticky="e")
    
    def _create_main_area(self):
        """Создание основной рабочей области"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Заглушка для контента
        self.content_label = ctk.CTkLabel(
            self.main_frame,
            text="Выберите раздел в меню",
            font=ctk.CTkFont(size=24)
        )
        self.content_label.grid(row=0, column=0, sticky="nsew")
        
        # Инициализация фреймов модулей
        self._init_module_frames()
    
    def _init_module_frames(self):
        """Инициализация фреймов модулей"""
        self.products_frame = None  # Будет создан при первом открытии
    
    def _create_statusbar(self):
        """Создание строки состояния"""
        self.statusbar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.statusbar.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self.statusbar,
            text="✓ Готов к работе | v1.0.0",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10)
    
    def _bind_hotkeys(self):
        """Привязка горячих клавиш"""
        self.bind("<F2>", lambda e: self._on_products())
        self.bind("<F5>", lambda e: self._refresh())
        self.bind("<Control-n>", lambda e: self._on_sales())
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
    
    def _toggle_fullscreen(self, event=None):
        """Переключение полноэкранного режима"""
        current = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not current)
    
    def _refresh(self):
        """Обновление текущего раздела"""
        logger.info("Обновление данных")
        self.update_status("Данные обновлены")
    
    # Обработчики навигации
    def _on_dashboard(self):
        self._show_dashboard()
    
    def _on_products(self):
        self._show_products()
    
    def _on_customers(self):
        self._show_customers()
    
    def _on_sales(self):
        self._show_sales()
    
    def _on_warehouse(self):
        self._show_warehouse()
    
    def _on_reports(self):
        self._show_reports()
    
    def _on_settings(self):
        self._show_settings()
    
    def _show_dashboard(self):
        """Показать панель управления"""
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()
        
        self.content_label.grid(row=0, column=0, sticky="nsew")
        self.section_title.configure(text="Панель управления")
        self._set_section("Панель управления")
    
    def _show_products(self):
        """Показать управление товарами"""
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()
        
        if self.products_frame is None:
            self.products_frame = ProductsFrame(
                self.main_frame, 
                self.app_controller.db_connection
            )
        
        self.products_frame.grid(row=0, column=0, sticky="nsew")
        self.section_title.configure(text="Каталог товаров")
        logger.info("Переход в раздел: Товары")
    
    def _show_customers(self):
        """Показать клиентов"""
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()
        
        if not hasattr(self, 'customers_frame') or self.customers_frame is None:
            from .customers_frame import CustomersFrame
            self.customers_frame = CustomersFrame(
                self.main_frame, 
                self.app_controller.db_connection
            )
        
        self.customers_frame.grid(row=0, column=0, sticky="nsew")
        self.section_title.configure(text="Клиенты")
        logger.info("Переход в раздел: Клиенты")
    
    def _show_sales(self):
        """Показать продажи"""
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()
        
        if not hasattr(self, 'sales_frame') or self.sales_frame is None:
            from .sales_frame import SalesFrame
            self.sales_frame = SalesFrame(
                self.main_frame, 
                self.app_controller.db_connection
            )
        
        self.sales_frame.grid(row=0, column=0, sticky="nsew")
        self.section_title.configure(text="Продажи")
        logger.info("Переход в раздел: Продажи")
    
    def _show_warehouse(self):
        """Показать склад"""
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()
        
        if not hasattr(self, 'warehouse_frame') or self.warehouse_frame is None:
            from .warehouse_frame import WarehouseFrame
            self.warehouse_frame = WarehouseFrame(
                self.main_frame, 
                self.app_controller.db_connection
            )
        
        self.warehouse_frame.grid(row=0, column=0, sticky="nsew")
        self.section_title.configure(text="Склад")
        logger.info("Переход в раздел: Склад")
    
    def _show_reports(self):
        """Показать отчёты"""
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()
        
        if not hasattr(self, 'reports_frame') or self.reports_frame is None:
            from .reports_frame import ReportsFrame
            self.reports_frame = ReportsFrame(
                self.main_frame, 
                self.app_controller.db_connection
            )
        
        self.reports_frame.grid(row=0, column=0, sticky="nsew")
        self.section_title.configure(text="Отчёты")
        logger.info("Переход в раздел: Отчёты")
    
    def _show_settings(self):
        """Показать настройки"""
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()
        
        if not hasattr(self, 'settings_frame') or self.settings_frame is None:
            from .settings_frame import SettingsFrame
            self.settings_frame = SettingsFrame(
                self.main_frame, 
                self.app_controller.db_connection,
                self.app_controller
            )
        
        self.settings_frame.grid(row=0, column=0, sticky="nsew")
        self.section_title.configure(text="Настройки")
        logger.info("Переход в раздел: Настройки")
    
    def _on_logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти?"):
            self.destroy()
            self.app_controller.main_window = None
            self.app_controller.show_login()
    
    def _set_section(self, title: str):
        """Установка заголовка раздела"""
        self.section_title.configure(text=title)
        logger.info(f"Переход в раздел: {title}")
    
    def set_user(self, user_info: dict):
        """Установка информации о текущем пользователе"""
        self.current_user = user_info
        self.user_info.configure(text=f"{user_info['full_name']} ({user_info['role']})")
    
    def update_status(self, message: str):
        """Обновление строки состояния"""
        self.status_label.configure(text=f"✓ {message} | v1.0.0")
