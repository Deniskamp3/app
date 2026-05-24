"""
Модуль оформления продаж (касса)
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SalesFrame(ctk.CTkFrame):
    """Фрейм оформления продаж"""
    
    def __init__(self, parent, db_connection, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_connection
        self.cart = []  # Корзина товаров
        
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_product_panel()
        self._create_cart_panel()
        
    def _create_product_panel(self):
        """Панель выбора товаров"""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Поиск товара
        search_frame = ctk.CTkFrame(panel)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Поиск товара...", width=250)
        self.search_entry.pack(side="left", padx=(0, 10))
        ctk.CTkButton(search_frame, text="🔍", command=self._search_products, width=50).pack(side="left")
        
        # Таблица товаров
        table_frame = ctk.CTkFrame(panel)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        columns = ("id", "name", "price", "stock")
        self.products_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.products_tree.heading("id", text="ID")
        self.products_tree.heading("name", text="Название")
        self.products_tree.heading("price", text="Цена")
        self.products_tree.heading("stock", text="Остаток")
        
        self.products_tree.column("id", width=50, anchor="center")
        self.products_tree.column("name", width=250)
        self.products_tree.column("price", width=80, anchor="e")
        self.products_tree.column("stock", width=70, anchor="center")
        
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.products_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        # Кнопка добавления в корзину
        ctk.CTkButton(panel, text="➕ В корзину", command=self._add_to_cart, fg_color="#28a745").pack(pady=10)
        
        self._load_products()
    
    def _create_cart_panel(self):
        """Панель корзины"""
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(panel, text="🛒 Корзина", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Таблица корзины
        cart_frame = ctk.CTkFrame(panel)
        cart_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        columns = ("name", "qty", "price", "total")
        self.cart_tree = ttk.Treeview(cart_frame, columns=columns, show="headings")
        
        self.cart_tree.heading("name", text="Товар")
        self.cart_tree.heading("qty", text="Кол-во")
        self.cart_tree.heading("price", text="Цена")
        self.cart_tree.heading("total", text="Сумма")
        
        self.cart_tree.column("name", width=150)
        self.cart_tree.column("qty", width=60, anchor="center")
        self.cart_tree.column("price", width=70, anchor="e")
        self.cart_tree.column("total", width=80, anchor="e")
        
        v_scrollbar = ttk.Scrollbar(cart_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.cart_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        # Итого
        self.total_label = ctk.CTkLabel(panel, text="Итого: 0.00 ₽", font=ctk.CTkFont(size=18, weight="bold"))
        self.total_label.pack(pady=10)
        
        # Клиент
        customer_frame = ctk.CTkFrame(panel)
        customer_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(customer_frame, text="Клиент:").pack(side="left", padx=5)
        self.customer_combo = ctk.CTkComboBox(customer_frame, values=["Розничный покупатель"])
        self.customer_combo.pack(side="left", fill="x", expand=True, padx=5)
        self._load_customers()
        
        # Кнопки действий
        btn_frame = ctk.CTkFrame(panel)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(btn_frame, text="🗑️ Очистить", command=self._clear_cart, fg_color="#dc3545").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="💰 Оформить продажу", command=self._complete_sale, fg_color="#28a745").pack(side="right", padx=5)
    
    def _load_products(self, search=""):
        """Загрузка списка товаров"""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        try:
            query = """
                SELECT p.id, p.name, p.price, p.quantity 
                FROM products p 
                WHERE p.quantity > 0
            """
            params = []
            
            if search:
                query += " AND (p.name LIKE ? OR p.article LIKE ?)"
                params = [f"%{search}%", f"%{search}%"]
            
            cursor = self.db.execute(query, params)
            products = cursor.fetchall()
            
            for p in products:
                self.products_tree.insert("", "end", values=(p[0], p[1], f"{p[2]:.2f}", p[3]))
        except Exception as e:
            logger.error(f"Ошибка загрузки товаров: {e}")
    
    def _load_customers(self):
        """Загрузка списка клиентов"""
        try:
            cursor = self.db.execute("SELECT name FROM customers ORDER BY name")
            customers = [row[0] for row in cursor.fetchall()]
            current = self.customer_combo.get()
            self.customer_combo.configure(values=["Розничный покупатель"] + customers)
            if current in customers:
                self.customer_combo.set(current)
        except Exception as e:
            logger.error(f"Ошибка загрузки клиентов: {e}")
    
    def _search_products(self):
        """Поиск товаров"""
        search = self.search_entry.get().strip()
        self._load_products(search)
    
    def _add_to_cart(self):
        """Добавление товара в корзину"""
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите товар")
            return
        
        item = self.products_tree.item(selected[0])
        product_id, name, price, stock = item['values']
        price = float(price)
        
        # Диалог количества
        dialog = ctk.CTkToplevel(self)
        dialog.title("Количество")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=f"Товар: {name}").pack(pady=10)
        qty_entry = ctk.CTkEntry(dialog, placeholder_text="Кол-во")
        qty_entry.pack(pady=10)
        qty_entry.insert(0, "1")
        
        def confirm():
            try:
                qty = int(qty_entry.get())
                if qty <= 0 or qty > stock:
                    messagebox.showerror("Ошибка", f"Доступно: {stock}")
                    return
                
                # Добавляем в корзину
                for cart_item in self.cart:
                    if cart_item['id'] == product_id:
                        cart_item['qty'] += qty
                        self._update_cart_display()
                        dialog.destroy()
                        return
                
                self.cart.append({
                    'id': product_id,
                    'name': name,
                    'price': price,
                    'qty': qty,
                    'stock': stock
                })
                self._update_cart_display()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите число")
        
        ctk.CTkButton(dialog, text="OK", command=confirm).pack(pady=10)
    
    def _update_cart_display(self):
        """Обновление отображения корзины"""
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        total = 0
        for item in self.cart:
            item_total = item['price'] * item['qty']
            total += item_total
            self.cart_tree.insert("", "end", values=(
                item['name'], item['qty'], f"{item['price']:.2f}", f"{item_total:.2f}"
            ))
        
        self.total_label.configure(text=f"Итого: {total:.2f} ₽")
    
    def _clear_cart(self):
        """Очистка корзины"""
        self.cart = []
        self._update_cart_display()
    
    def _complete_sale(self):
        """Оформление продажи"""
        if not self.cart:
            messagebox.showwarning("Предупреждение", "Корзина пуста")
            return
        
        customer_name = self.customer_combo.get()
        
        if messagebox.askyesno("Подтверждение", f"Оформить продажу на {self.total_label.cget('text')}?"):
            try:
                # Получаем ID клиента
                cursor = self.db.execute("SELECT id FROM customers WHERE name = ?", (customer_name,))
                row = cursor.fetchone()
                customer_id = row[0] if row else None
                
                # Создаём продажу
                total = sum(item['price'] * item['qty'] for item in self.cart)
                
                cursor = self.db.execute("""
                    INSERT INTO sales (customer_id, total_amount, status)
                    VALUES (?, ?, 'completed')
                """, (customer_id, total))
                sale_id = cursor.lastrowid
                
                # Добавляем позиции
                for item in self.cart:
                    self.db.execute("""
                        INSERT INTO sale_items (sale_id, product_id, quantity, price)
                        VALUES (?, ?, ?, ?)
                    """, (sale_id, item['id'], item['qty'], item['price']))
                    
                    # Уменьшаем остаток
                    self.db.execute("""
                        UPDATE products SET quantity = quantity - ? WHERE id = ?
                    """, (item['qty'], item['id']))
                
                self.db.commit()
                
                messagebox.showinfo("Успех", f"Продажа №{sale_id} оформлена!\nСумма: {total:.2f} ₽")
                logger.info(f"Продажа №{sale_id} оформлена на сумму {total:.2f} ₽")
                
                self._clear_cart()
                self._load_products()
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Ошибка оформления продажи: {e}")
                messagebox.showerror("Ошибка", f"Не удалось оформить продажу: {e}")
