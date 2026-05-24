"""
Модуль управления товарами
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Optional, Callable
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ProductsFrame(ctk.CTkFrame):
    """Фрейм управления товарами"""
    
    def __init__(self, parent, db_connection, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_connection
        
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Создание интерфейса
        self._create_toolbar()
        self._create_table()
        
    def _create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Поиск
        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Поиск по названию или артикулу...",
            width=300
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        
        search_btn = ctk.CTkButton(
            toolbar,
            text="🔍 Найти",
            command=self._search_products,
            width=100
        )
        search_btn.pack(side="left", padx=5)
        
        # Кнопки действий
        add_btn = ctk.CTkButton(
            toolbar,
            text="➕ Добавить товар",
            command=self._add_product,
            fg_color="#28a745",
            hover_color="#218838"
        )
        add_btn.pack(side="left", padx=5)
        
        edit_btn = ctk.CTkButton(
            toolbar,
            text="✏️ Редактировать",
            command=self._edit_product,
            fg_color="#007bff",
            hover_color="#0069d9"
        )
        edit_btn.pack(side="left", padx=5)
        
        delete_btn = ctk.CTkButton(
            toolbar,
            text="🗑️ Удалить",
            command=self._delete_product,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        delete_btn.pack(side="left", padx=5)
        
        import_btn = ctk.CTkButton(
            toolbar,
            text="📥 Импорт из Excel",
            command=self._import_from_excel,
            fg_color="#6f42c1",
            hover_color="#5a32a3"
        )
        import_btn.pack(side="right", padx=5)
        
        refresh_btn = ctk.CTkButton(
            toolbar,
            text="🔄 Обновить",
            command=self._refresh_table,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        refresh_btn.pack(side="right", padx=5)
    
    def _create_table(self):
        """Создание таблицы товаров"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Определение колонок
        columns = ("id", "article", "name", "category", "price", "quantity", "unit")
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Настройка заголовков
        self.tree.heading("id", text="ID")
        self.tree.heading("article", text="Артикул")
        self.tree.heading("name", text="Наименование")
        self.tree.heading("category", text="Категория")
        self.tree.heading("price", text="Цена, ₽")
        self.tree.heading("quantity", text="Остаток")
        self.tree.heading("unit", text="Ед.изм.")
        
        # Настройка ширины колонок
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("article", width=100, anchor="center")
        self.tree.column("name", width=250, anchor="w")
        self.tree.column("category", width=150, anchor="w")
        self.tree.column("price", width=100, anchor="e")
        self.tree.column("quantity", width=80, anchor="center")
        self.tree.column("unit", width=80, anchor="center")
        
        # Скроллбары
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Размещение
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # Загрузка данных
        self._refresh_table()
    
    def _refresh_table(self):
        """Обновление таблицы товаров"""
        try:
            # Очистка таблицы
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Загрузка данных из БД
            cursor = self.db.execute("""
                SELECT p.id, p.article, p.name, c.name as category, 
                       p.price, p.quantity, p.unit
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.name
            """)
            
            products = cursor.fetchall()
            
            for product in products:
                self.tree.insert("", "end", values=product)
            
            logger.info(f"Загружено {len(products)} товаров")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки товаров: {e}")
            messagebox.showerror("Ошибка", f"Не удалось загрузить товары: {e}")
    
    def _search_products(self):
        """Поиск товаров"""
        query = self.search_entry.get().strip()
        
        if not query:
            self._refresh_table()
            return
        
        try:
            # Очистка таблицы
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Поиск в БД
            cursor = self.db.execute("""
                SELECT p.id, p.article, p.name, c.name as category, 
                       p.price, p.quantity, p.unit
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.name LIKE ? OR p.article LIKE ?
                ORDER BY p.name
            """, (f"%{query}%", f"%{query}%"))
            
            products = cursor.fetchall()
            
            for product in products:
                self.tree.insert("", "end", values=product)
            
            logger.info(f"Найдено {len(products)} товаров по запросу '{query}'")
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            messagebox.showerror("Ошибка", f"Не удалось выполнить поиск: {e}")
    
    def _add_product(self):
        """Добавление товара"""
        dialog = ProductDialog(self, self.db, title="Добавление товара")
        if dialog.result:
            self._refresh_table()
    
    def _edit_product(self):
        """Редактирование товара"""
        selected = self.tree.selection()
        
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите товар для редактирования")
            return
        
        item = self.tree.item(selected[0])
        product_id = item['values'][0]
        
        dialog = ProductDialog(self, self.db, product_id=product_id, title="Редактирование товара")
        if dialog.result:
            self._refresh_table()
    
    def _delete_product(self):
        """Удаление товара"""
        selected = self.tree.selection()
        
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите товар для удаления")
            return
        
        item = self.tree.item(selected[0])
        product_id = item['values'][0]
        product_name = item['values'][2]
        
        if messagebox.askyesno("Подтверждение", f"Удалить товар '{product_name}'?"):
            try:
                self.db.execute("DELETE FROM products WHERE id = ?", (product_id,))
                self.db.commit()
                self._refresh_table()
                logger.info(f"Удалён товар ID={product_id}")
            except Exception as e:
                logger.error(f"Ошибка удаления: {e}")
                messagebox.showerror("Ошибка", f"Не удалось удалить товар: {e}")
    
    def _import_from_excel(self):
        """Импорт из Excel"""
        messagebox.showinfo("Инфо", "Функция импорта будет реализована в следующей версии")


class ProductDialog(ctk.CTkToplevel):
    """Диалог добавления/редактирования товара"""
    
    def __init__(self, parent, db_connection, product_id=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.db = db_connection
        self.product_id = product_id
        self.result = False
        
        # Настройка окна
        self.title(kwargs.get('title', 'Товар'))
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Загрузка данных если редактирование
        if product_id:
            self._load_product()
        
        # Создание интерфейса
        self._create_form()
        
        # Модальность
        self.transient(parent)
        self.grab_set()
        
        # Центрирование
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _load_product(self):
        """Загрузка данных товара"""
        cursor = self.db.execute(
            "SELECT * FROM products WHERE id = ?", (self.product_id,)
        )
        self.product_data = cursor.fetchone()
    
    def _create_form(self):
        """Создание формы"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Артикул
        ctk.CTkLabel(main_frame, text="Артикул:").grid(row=0, column=0, sticky="w", pady=5)
        self.article_entry = ctk.CTkEntry(main_frame, width=300)
        self.article_entry.grid(row=0, column=1, pady=5)
        
        # Наименование
        ctk.CTkLabel(main_frame, text="Наименование:").grid(row=1, column=0, sticky="w", pady=5)
        self.name_entry = ctk.CTkEntry(main_frame, width=300)
        self.name_entry.grid(row=1, column=1, pady=5)
        
        # Категория
        ctk.CTkLabel(main_frame, text="Категория:").grid(row=2, column=0, sticky="w", pady=5)
        self.category_combo = ctk.CTkComboBox(main_frame, width=300, values=self._get_categories())
        self.category_combo.grid(row=2, column=1, pady=5)
        
        # Цена
        ctk.CTkLabel(main_frame, text="Цена (₽):").grid(row=3, column=0, sticky="w", pady=5)
        self.price_entry = ctk.CTkEntry(main_frame, width=300)
        self.price_entry.grid(row=3, column=1, pady=5)
        
        # Количество
        ctk.CTkLabel(main_frame, text="Остаток:").grid(row=4, column=0, sticky="w", pady=5)
        self.quantity_entry = ctk.CTkEntry(main_frame, width=300)
        self.quantity_entry.grid(row=4, column=1, pady=5)
        
        # Единица измерения
        ctk.CTkLabel(main_frame, text="Ед.изм.:").grid(row=5, column=0, sticky="w", pady=5)
        self.unit_combo = ctk.CTkComboBox(
            main_frame, 
            width=300, 
            values=["шт", "кг", "м", "м²", "м³", "л", "упак", "коробка"]
        )
        self.unit_combo.grid(row=5, column=1, pady=5)
        self.unit_combo.set("шт")
        
        # Описание
        ctk.CTkLabel(main_frame, text="Описание:").grid(row=6, column=0, sticky="nw", pady=5)
        self.desc_text = ctk.CTkTextbox(main_frame, width=300, height=100)
        self.desc_text.grid(row=6, column=1, pady=5)
        
        # Кнопки
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Сохранить",
            command=self._save,
            fg_color="#28a745",
            hover_color="#218838",
            width=120
        )
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="❌ Отмена",
            command=self.destroy,
            fg_color="#6c757d",
            hover_color="#5a6268",
            width=120
        )
        cancel_btn.pack(side="left", padx=10)
        
        # Заполнение данными если редактирование
        if self.product_id and hasattr(self, 'product_data') and self.product_data:
            p = self.product_data
            self.article_entry.insert(0, p[2] or '')
            self.name_entry.insert(0, p[3])
            self.price_entry.insert(0, str(p[4]))
            self.quantity_entry.insert(0, str(p[5]))
            self.unit_combo.set(p[6] or 'шт')
            if p[7]:
                self.desc_text.insert("0.0", p[7])
    
    def _get_categories(self):
        """Получение списка категорий"""
        try:
            cursor = self.db.execute("SELECT name FROM categories ORDER BY name")
            return [row[0] for row in cursor.fetchall()]
        except:
            return []
    
    def _save(self):
        """Сохранение товара"""
        try:
            article = self.article_entry.get().strip()
            name = self.name_entry.get().strip()
            category = self.category_combo.get()
            price = float(self.price_entry.get().replace(',', '.'))
            quantity = int(self.quantity_entry.get())
            unit = self.unit_combo.get()
            description = self.desc_text.get("0.0", "end-1c").strip()
            
            if not name:
                messagebox.showwarning("Предупреждение", "Введите наименование товара")
                return
            
            # Получаем ID категории
            category_id = None
            if category:
                cursor = self.db.execute(
                    "SELECT id FROM categories WHERE name = ?", (category,)
                )
                row = cursor.fetchone()
                if row:
                    category_id = row[0]
            
            if self.product_id:
                # Обновление
                self.db.execute("""
                    UPDATE products SET article=?, name=?, category_id=?, 
                           price=?, quantity=?, unit=?, description=?
                    WHERE id=?
                """, (article, name, category_id, price, quantity, unit, description, self.product_id))
            else:
                # Добавление
                self.db.execute("""
                    INSERT INTO products (article, name, category_id, price, quantity, unit, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (article, name, category_id, price, quantity, unit, description))
            
            self.db.commit()
            self.result = True
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Цена и количество должны быть числами")
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить товар: {e}")
