"""
Модуль окна авторизации
"""

import customtkinter as ctk
from tkinter import messagebox
import logging

logger = logging.getLogger(__name__)


class LoginWindow(ctk.CTkToplevel):
    """Окно авторизации пользователя"""
    
    def __init__(self, app_controller, **kwargs):
        super().__init__(**kwargs)
        
        self.app_controller = app_controller
        
        # Настройка окна
        self.title("Вход в систему - СтройУчёт")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Центрирование окна
        self._center_window()
        
        # Создание интерфейса
        self._create_widgets()
        
        # Привязка клавиши Enter
        self.bind("<Return>", lambda e: self._on_login())
    
    def _center_window(self):
        """Центрирование окна на экране"""
        self.update_idletasks()
        width = 400
        height = 500
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """Создание виджетов окна"""
        # Основной фрейм
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Логотип
        logo_label = ctk.CTkLabel(
            main_frame,
            text="🏗️\nСтройУчёт",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        logo_label.pack(pady=(40, 10))
        
        version_label = ctk.CTkLabel(
            main_frame,
            text="v1.0.0 | Система учёта продаж",
            font=ctk.CTkFont(size=12)
        )
        version_label.pack(pady=(0, 30))
        
        # Поле логина
        login_label = ctk.CTkLabel(main_frame, text="Логин:")
        login_label.pack(anchor="w", padx=20)
        
        self.login_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Введите логин",
            height=40
        )
        self.login_entry.pack(fill="x", padx=20, pady=(5, 20))
        
        # Поле пароля
        password_label = ctk.CTkLabel(main_frame, text="Пароль:")
        password_label.pack(anchor="w", padx=20)
        
        self.password_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Введите пароль",
            show="•",
            height=40
        )
        self.password_entry.pack(fill="x", padx=20, pady=(5, 20))
        
        # Кнопка входа
        login_btn = ctk.CTkButton(
            main_frame,
            text="Войти",
            command=self._on_login,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        login_btn.pack(fill="x", padx=20, pady=(20, 10))
        
        # Статус бар
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            text_color="#DC3545",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=(10, 0))
        
        # Фокус на поле логина
        self.login_entry.focus()
    
    def _on_login(self):
        """Обработчик кнопки входа"""
        username = self.login_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            self.status_label.configure(text="Введите логин и пароль")
            return
        
        # Вызов сервиса аутентификации
        result = self.app_controller.authenticate(username, password)
        
        if result['success']:
            logger.info(f"Успешный вход: {username}")
            self.destroy()
            self.app_controller.show_main(result['user'])
        else:
            self.status_label.configure(text=result['message'])
            self.password_entry.delete(0, 'end')
            logger.warning(f"Неудачная попытка входа: {username}")
    
    def set_status(self, message: str):
        """Установка сообщения статуса"""
        self.status_label.configure(text=message)
    
    def clear_fields(self):
        """Очистка полей ввода"""
        self.login_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.login_entry.focus()
