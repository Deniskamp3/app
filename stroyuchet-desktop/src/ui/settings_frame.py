"""
Модуль настроек приложения
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
import os
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)


class SettingsFrame(ctk.CTkFrame):
    """Фрейм настроек"""
    
    def __init__(self, parent, db_connection, app_controller, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_connection
        self.app_controller = app_controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_settings_area()
    
    def _create_settings_area(self):
        """Область настроек"""
        settings_frame = ctk.CTkScrollableFrame(self)
        settings_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Настройки компании
        company_frame = ctk.CTkFrame(settings_frame)
        company_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(company_frame, text="🏢 Настройки компании", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.company_entries = {}
        labels = ["Название организации", "ИНН", "Адрес", "Телефон"]
        keys = ["name", "inn", "address", "phone"]
        
        for i, label in enumerate(labels):
            ctk.CTkLabel(company_frame, text=label).pack(anchor="w", padx=20, pady=(5, 0))
            entry = ctk.CTkEntry(company_frame, width=400)
            entry.pack(padx=20, pady=5)
            self.company_entries[keys[i]] = entry
        
        # Загрузка текущих значений
        self._load_company_settings()
        
        # Бэкапы
        backup_frame = ctk.CTkFrame(settings_frame)
        backup_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(backup_frame, text="💾 Резервное копирование", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(backup_frame)
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="📥 Создать бэкап сейчас", command=self._create_backup, fg_color="#28a745").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📂 Открыть папку бэкапов", command=self._open_backups_folder, fg_color="#007bff").pack(side="left", padx=10)
        
        # Информация о БД
        info_frame = ctk.CTkFrame(settings_frame)
        info_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(info_frame, text="ℹ️ Информация о базе данных", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        try:
            cursor = self.db.execute("SELECT COUNT(*) FROM products")
            products_count = cursor.fetchone()[0]
            
            cursor = self.db.execute("SELECT COUNT(*) FROM sales")
            sales_count = cursor.fetchone()[0]
            
            cursor = self.db.execute("SELECT COUNT(*) FROM customers")
            customers_count = cursor.fetchone()[0]
        except:
            products_count = sales_count = customers_count = 0
        
        ctk.CTkLabel(info_frame, text=f"Товаров: {products_count}").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text=f"Продаж: {sales_count}").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text=f"Клиентов: {customers_count}").pack(anchor="w", padx=20, pady=5)
        
        # Пользователи
        users_frame = ctk.CTkFrame(settings_frame)
        users_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(users_frame, text="👥 Управление пользователями", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkButton(users_frame, text="➕ Добавить пользователя", command=self._add_user, fg_color="#28a745").pack(pady=10)
        ctk.CTkButton(users_frame, text="🔑 Сменить пароль", command=self._change_password, fg_color="#ffc107").pack(pady=10)
        
        # Тема оформления
        theme_frame = ctk.CTkFrame(settings_frame)
        theme_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(theme_frame, text="🎨 Тема оформления", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.theme_var = ctk.StringVar(value="system")
        themes = [("Системная", "system"), ("Светлая", "light"), ("Тёмная", "dark")]
        
        for text, value in themes:
            ctk.CTkRadioButton(theme_frame, text=text, variable=self.theme_var, value=value, 
                             command=self._change_theme).pack(side="left", padx=20)
        
        # Сохранение настроек компании
        save_btn = ctk.CTkButton(settings_frame, text="💾 Сохранить настройки компании", 
                                command=self._save_company_settings, 
                                fg_color="#28a745", height=40)
        save_btn.pack(pady=20)
    
    def _load_company_settings(self):
        """Загрузка настроек компании"""
        try:
            cursor = self.db.execute("SELECT key, value FROM app_settings WHERE key IN ('company_name', 'company_inn', 'company_address', 'company_phone')")
            settings = {row[0]: row[1] for row in cursor.fetchall()}
            
            mapping = {
                'company_name': 'name',
                'company_inn': 'inn',
                'company_address': 'address',
                'company_phone': 'phone'
            }
            
            for db_key, ui_key in mapping.items():
                if db_key in settings:
                    self.company_entries[ui_key].delete(0, 'end')
                    self.company_entries[ui_key].insert(0, settings[db_key])
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
    
    def _save_company_settings(self):
        """Сохранение настроек компании"""
        try:
            mapping = {
                'name': 'company_name',
                'inn': 'company_inn',
                'address': 'company_address',
                'phone': 'company_phone'
            }
            
            for ui_key, db_key in mapping.items():
                value = self.company_entries[ui_key].get().strip()
                
                cursor = self.db.execute("SELECT 1 FROM app_settings WHERE key = ?", (db_key,))
                if cursor.fetchone():
                    self.db.execute("UPDATE app_settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?", (value, db_key))
                else:
                    self.db.execute("INSERT INTO app_settings (key, value) VALUES (?, ?)", (db_key, value))
            
            self.db.commit()
            messagebox.showinfo("Успех", "Настройки компании сохранены")
            logger.info("Настройки компании сохранены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
            logger.error(f"Ошибка сохранения настроек: {e}")
    
    def _create_backup(self):
        """Создание резервной копии"""
        try:
            from pathlib import Path
            
            backup_dir = Path.home() / "AppData" / "Roaming" / "StroyUchet" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_{timestamp}.db"
            
            # Копируем БД
            db_path = Path.home() / "AppData" / "Roaming" / "StroyUchet" / "database.db"
            shutil.copy2(db_path, backup_file)
            
            messagebox.showinfo("Успех", f"Бэкап создан:\n{backup_file}")
            logger.info(f"Создан бэкап: {backup_file}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать бэкап: {e}")
            logger.error(f"Ошибка создания бэкапа: {e}")
    
    def _open_backups_folder(self):
        """Открытие папки бэкапов"""
        try:
            backup_dir = os.path.join(os.getenv('APPDATA'), 'StroyUchet', 'backups')
            os.startfile(backup_dir)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")
    
    def _add_user(self):
        """Добавление пользователя"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавление пользователя")
        dialog.geometry("350x300")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Логин:").pack(pady=(20, 5))
        login_entry = ctk.CTkEntry(dialog)
        login_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Пароль:").pack(pady=(10, 5))
        password_entry = ctk.CTkEntry(dialog, show="*")
        password_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="ФИО:").pack(pady=(10, 5))
        name_entry = ctk.CTkEntry(dialog)
        name_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Роль:").pack(pady=(10, 5))
        role_combo = ctk.CTkComboBox(dialog, values=["admin", "manager", "seller"])
        role_combo.set("seller")
        role_combo.pack(pady=5)
        
        def save():
            try:
                login = login_entry.get().strip()
                password = password_entry.get().strip()
                name = name_entry.get().strip()
                role = role_combo.get()
                
                if not login or not password:
                    messagebox.showerror("Ошибка", "Логин и пароль обязательны")
                    return
                
                import bcrypt
                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                
                self.db.execute("""
                    INSERT INTO users (username, password_hash, full_name, role)
                    VALUES (?, ?, ?, ?)
                """, (login, hashed, name, role))
                self.db.commit()
                
                messagebox.showinfo("Успех", "Пользователь добавлен")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось добавить пользователя: {e}")
        
        ctk.CTkButton(dialog, text="Сохранить", command=save, fg_color="#28a745").pack(pady=20)
    
    def _change_password(self):
        """Смена пароля"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Смена пароля")
        dialog.geometry("300x200")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Текущий пароль:").pack(pady=(20, 5))
        old_pass = ctk.CTkEntry(dialog, show="*")
        old_pass.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Новый пароль:").pack(pady=(10, 5))
        new_pass = ctk.CTkEntry(dialog, show="*")
        new_pass.pack(pady=5)
        
        def change():
            try:
                current_user = self.app_controller.current_user
                if not current_user:
                    return
                
                import bcrypt
                
                # Проверяем текущий пароль
                cursor = self.db.execute("SELECT password_hash FROM users WHERE id = ?", (current_user['id'],))
                stored_hash = cursor.fetchone()[0]
                
                if not bcrypt.checkpw(old_pass.get().encode(), stored_hash.encode()):
                    messagebox.showerror("Ошибка", "Неверный текущий пароль")
                    return
                
                # Меняем пароль
                new_hash = bcrypt.hashpw(new_pass.get().encode(), bcrypt.gensalt()).decode()
                self.db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, current_user['id']))
                self.db.commit()
                
                messagebox.showinfo("Успех", "Пароль изменён")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {e}")
        
        ctk.CTkButton(dialog, text="Изменить", command=change, fg_color="#ffc107").pack(pady=20)
    
    def _change_theme(self):
        """Смена темы"""
        theme = self.theme_var.get()
        ctk.set_appearance_mode(theme)
        logger.info(f"Тема изменена на: {theme}")
