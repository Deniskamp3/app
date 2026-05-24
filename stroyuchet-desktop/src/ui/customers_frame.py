"""
Модуль управления клиентами
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)


class CustomersFrame(ctk.CTkFrame):
    """Фрейм управления клиентами"""
    
    def __init__(self, parent, db_connection, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_connection
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_toolbar()
        self._create_table()
        
    def _create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.search_entry = ctk.CTkEntry(toolbar, placeholder_text="Поиск по имени или телефону...", width=300)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(toolbar, text="🔍 Найти", command=self._search_customers, width=100).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="➕ Добавить клиента", command=self._add_customer, fg_color="#28a745").pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="✏️ Редактировать", command=self._edit_customer, fg_color="#007bff").pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="🗑️ Удалить", command=self._delete_customer, fg_color="#dc3545").pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="🔄 Обновить", command=self._refresh_table, fg_color="#6c757d").pack(side="right", padx=5)
    
    def _create_table(self):
        """Создание таблицы клиентов"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        columns = ("id", "name", "phone", "email", "address", "discount")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="ФИО/Название")
        self.tree.heading("phone", text="Телефон")
        self.tree.heading("email", text="Email")
        self.tree.heading("address", text="Адрес")
        self.tree.heading("discount", text="Скидка %")
        
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("phone", width=120)
        self.tree.column("email", width=150)
        self.tree.column("address", width=200)
        self.tree.column("discount", width=80, anchor="center")
        
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        self._refresh_table()
    
    def _refresh_table(self):
        """Обновление таблицы"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            cursor = self.db.execute("""
                SELECT id, name, phone, email, address, discount 
                FROM customers 
                ORDER BY name
            """)
            customers = cursor.fetchall()
            
            for c in customers:
                self.tree.insert("", "end", values=c)
            
            logger.info(f"Загружено {len(customers)} клиентов")
        except Exception as e:
            logger.error(f"Ошибка загрузки клиентов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить клиентов: {e}")
    
    def _search_customers(self):
        """Поиск клиентов"""
        query = self.search_entry.get().strip()
        
        if not query:
            self._refresh_table()
            return
        
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            cursor = self.db.execute("""
                SELECT id, name, phone, email, address, discount 
                FROM customers 
                WHERE name LIKE ? OR phone LIKE ?
                ORDER BY name
            """, (f"%{query}%", f"%{query}%"))
            
            customers = cursor.fetchall()
            for c in customers:
                self.tree.insert("", "end", values=c)
                
            logger.info(f"Найдено {len(customers)} клиентов")
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
    
    def _add_customer(self):
        """Добавление клиента"""
        dialog = CustomerDialog(self, self.db, title="Добавление клиента")
        if dialog.result:
            self._refresh_table()
    
    def _edit_customer(self):
        """Редактирование клиента"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите клиента для редактирования")
            return
        
        item = self.tree.item(selected[0])
        customer_id = item['values'][0]
        
        dialog = CustomerDialog(self, self.db, customer_id=customer_id, title="Редактирование клиента")
        if dialog.result:
            self._refresh_table()
    
    def _delete_customer(self):
        """Удаление клиента"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите клиента для удаления")
            return
        
        item = self.tree.item(selected[0])
        customer_id = item['values'][0]
        customer_name = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить клиента '{customer_name}'?"):
            try:
                self.db.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
                self.db.commit()
                self._refresh_table()
                logger.info(f"Удалён клиент ID={customer_id}")
            except Exception as e:
                logger.error(f"Ошибка удаления: {e}")
                messagebox.showerror("Ошибка", f"Не удалось удалить клиента: {e}")


class CustomerDialog(ctk.CTkToplevel):
    """Диалог добавления/редактирования клиента"""
    
    def __init__(self, parent, db_connection, customer_id=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.db = db_connection
        self.customer_id = customer_id
        self.result = False
        
        self.title(kwargs.get('title', 'Клиент'))
        self.geometry("450x400")
        self.resizable(False, False)
        
        if customer_id:
            self._load_customer()
        
        self._create_form()
        
        self.transient(parent)
        self.grab_set()
    
    def _load_customer(self):
        """Загрузка данных клиента"""
        cursor = self.db.execute("SELECT * FROM customers WHERE id = ?", (self.customer_id,))
        self.customer_data = cursor.fetchone()
    
    def _create_form(self):
        """Создание формы"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        labels = ["ФИО/Название", "Телефон", "Email", "Адрес", "Скидка (%)"]
        keys = ["name", "phone", "email", "address", "discount"]
        
        self.entries = {}
        for i, label in enumerate(labels):
            ctk.CTkLabel(main_frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            entry = ctk.CTkEntry(main_frame, width=300)
            entry.grid(row=i, column=1, pady=5)
            self.entries[keys[i]] = entry
        
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=20)
        
        ctk.CTkButton(btn_frame, text="💾 Сохранить", command=self._save, fg_color="#28a745", width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="❌ Отмена", command=self.destroy, fg_color="#6c757d", width=120).pack(side="left", padx=10)
        
        if self.customer_id and hasattr(self, 'customer_data') and self.customer_data:
            c = self.customer_data
            self.entries['name'].insert(0, c[1] or '')
            self.entries['phone'].insert(0, c[2] or '')
            self.entries['email'].insert(0, c[3] or '')
            self.entries['address'].insert(0, c[4] or '')
            self.entries['discount'].insert(0, str(c[5] or 0))
    
    def _save(self):
        """Сохранение клиента"""
        try:
            data = {k: v.get().strip() for k, v in self.entries.items()}
            
            if not data['name']:
                messagebox.showwarning("Предупреждение", "Введите имя клиента")
                return
            
            data['discount'] = float(data['discount'].replace(',', '.') or 0)
            
            if self.customer_id:
                self.db.execute("""
                    UPDATE customers SET name=?, phone=?, email=?, address=?, discount=?
                    WHERE id=?
                """, (data['name'], data['phone'], data['email'], data['address'], data['discount'], self.customer_id))
            else:
                self.db.execute("""
                    INSERT INTO customers (name, phone, email, address, discount)
                    VALUES (?, ?, ?, ?, ?)
                """, (data['name'], data['phone'], data['email'], data['address'], data['discount']))
            
            self.db.commit()
            self.result = True
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить клиента: {e}")
