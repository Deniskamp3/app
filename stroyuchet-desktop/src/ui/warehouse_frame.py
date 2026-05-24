"""
Модуль управления складом (остатки и поставки)
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)


class WarehouseFrame(ctk.CTkFrame):
    """Фрейм управления складом"""
    
    def __init__(self, parent, db_connection, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_connection
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_toolbar()
        self._create_table()
        
    def _create_toolbar(self):
        """Панель инструментов"""
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(toolbar, text="📦 Складской учёт", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        
        self.low_stock_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(toolbar, text="Только низкие остатки", variable=self.low_stock_var, command=self._refresh_table).pack(side="left", padx=10)
        
        ctk.CTkButton(toolbar, text="➕ Поступление", command=self._add_supply, fg_color="#28a745").pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="🔄 Обновить", command=self._refresh_table, fg_color="#6c757d").pack(side="right", padx=5)
    
    def _create_table(self):
        """Таблица остатков"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        columns = ("id", "article", "name", "category", "price", "quantity", "unit", "total_value")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("article", text="Артикул")
        self.tree.heading("name", text="Название")
        self.tree.heading("category", text="Категория")
        self.tree.heading("price", text="Цена")
        self.tree.heading("quantity", text="Остаток")
        self.tree.heading("unit", text="Ед.")
        self.tree.heading("total_value", text="На сумму")
        
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("article", width=100)
        self.tree.column("name", width=250)
        self.tree.column("category", width=120)
        self.tree.column("price", width=80, anchor="e")
        self.tree.column("quantity", width=80, anchor="center")
        self.tree.column("unit", width=60, anchor="center")
        self.tree.column("total_value", width=100, anchor="e")
        
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        self._refresh_table()
    
    def _refresh_table(self):
        """Обновление таблицы"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            query = """
                SELECT p.id, p.article, p.name, c.name, p.price, p.quantity, p.unit, 
                       (p.price * p.quantity) as total_value
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
            """
            
            if self.low_stock_var.get():
                query += " WHERE p.quantity < 10"
            
            query += " ORDER BY p.quantity ASC"
            
            cursor = self.db.execute(query)
            products = cursor.fetchall()
            
            for p in products:
                color = "white"
                if p[5] < 5:
                    color = "#ffcccc"  # Красный для критических остатков
                elif p[5] < 10:
                    color = "#fff3cd"  # Жёлтый для низких
                
                self.tree.insert("", "end", values=(p[0], p[1], p[2], p[3], f"{p[4]:.2f}", p[5], p[6], f"{p[7]:.2f}"))
            
            logger.info(f"Загружено {len(products)} позиций склада")
        except Exception as e:
            logger.error(f"Ошибка загрузки склада: {e}")
    
    def _add_supply(self):
        """Добавление поступления"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Инфо", "Выберите товар для оприходования")
            return
        
        item = self.tree.item(selected[0])
        product_id = item['values'][0]
        product_name = item['values'][2]
        current_qty = int(item['values'][5])
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Поступление товара")
        dialog.geometry("350x200")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=f"Товар: {product_name}").pack(pady=10)
        ctk.CTkLabel(dialog, text=f"Текущий остаток: {current_qty}").pack(pady=5)
        
        qty_entry = ctk.CTkEntry(dialog, placeholder_text="Количество поступления")
        qty_entry.pack(pady=10)
        
        def save():
            try:
                qty = int(qty_entry.get())
                if qty <= 0:
                    messagebox.showerror("Ошибка", "Количество должно быть положительным")
                    return
                
                self.db.execute("""
                    UPDATE products SET quantity = quantity + ? WHERE id = ?
                """, (qty, product_id))
                self.db.commit()
                
                messagebox.showinfo("Успех", f"Оприходовано {qty} шт.")
                self._refresh_table()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите число")
        
        ctk.CTkButton(dialog, text="Сохранить", command=save, fg_color="#28a745").pack(pady=10)
