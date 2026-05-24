"""
Модуль отчётов и аналитики
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ReportsFrame(ctk.CTkFrame):
    """Фрейм отчётов"""
    
    def __init__(self, parent, db_connection, **kwargs):
        super().__init__(parent, **kwargs)
        self.db = db_connection
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_toolbar()
        self._create_reports_area()
    
    def _create_toolbar(self):
        """Панель инструментов"""
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(toolbar, text="📈 Отчёты и аналитика", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        
        # Период
        ctk.CTkLabel(toolbar, text="Период:").pack(side="left", padx=(20, 5))
        
        self.period_var = ctk.StringVar(value="week")
        periods = [("Неделя", "week"), ("Месяц", "month"), ("Квартал", "quarter"), ("Год", "year")]
        
        for text, value in periods:
            ctk.CTkRadioButton(toolbar, text=text, variable=self.period_var, value=value, command=self._update_reports).pack(side="left", padx=5)
        
        # Экспорт
        ctk.CTkButton(toolbar, text="📥 Excel", command=lambda: messagebox.showinfo("Инфо", "Экспорт в Excel будет добавлен"), fg_color="#28a745").pack(side="right", padx=5)
        ctk.CTkButton(toolbar, text="📄 PDF", command=lambda: messagebox.showinfo("Инфо", "Экспорт в PDF будет добавлен"), fg_color="#dc3545").pack(side="right", padx=5)
    
    def _create_reports_area(self):
        """Область отчётов"""
        reports_frame = ctk.CTkScrollableFrame(self)
        reports_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # KPI карточки
        kpi_frame = ctk.CTkFrame(reports_frame)
        kpi_frame.pack(fill="x", pady=10)
        
        self.kpi_labels = {}
        kpis = [
            ("total_sales", "Всего продаж", "#007bff"),
            ("total_revenue", "Выручка", "#28a745"),
            ("avg_sale", "Средний чек", "#ffc107"),
            ("products_sold", "Товаров продано", "#17a2b8")
        ]
        
        for i, (key, title, color) in enumerate(kpis):
            card = ctk.CTkFrame(kpi_frame, fg_color=color, corner_radius=10)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            kpi_frame.grid_columnconfigure(i, weight=1)
            
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
            label = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(size=24, weight="bold"))
            label.pack(pady=(0, 10))
            self.kpi_labels[key] = label
        
        # Таблица продаж
        table_frame = ctk.CTkFrame(reports_frame)
        table_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(table_frame, text="Последние продажи", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        columns = ("id", "date", "customer", "amount", "status")
        self.sales_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.sales_tree.heading("id", text="№")
        self.sales_tree.heading("date", text="Дата")
        self.sales_tree.heading("customer", text="Клиент")
        self.sales_tree.heading("amount", text="Сумма")
        self.sales_tree.heading("status", text="Статус")
        
        self.sales_tree.column("id", width=50, anchor="center")
        self.sales_tree.column("date", width=120)
        self.sales_tree.column("customer", width=200)
        self.sales_tree.column("amount", width=100, anchor="e")
        self.sales_tree.column("status", width=100, anchor="center")
        
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.sales_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        self._update_reports()
    
    def _update_reports(self):
        """Обновление отчётов"""
        try:
            # Определяем период
            period = self.period_var.get()
            days = {"week": 7, "month": 30, "quarter": 90, "year": 365}[period]
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # KPI
            cursor = self.db.execute("""
                SELECT COUNT(*), COALESCE(SUM(total_amount), 0), 
                       COALESCE(AVG(total_amount), 0)
                FROM sales 
                WHERE date >= ? AND status = 'completed'
            """, (start_date,))
            row = cursor.fetchone()
            
            self.kpi_labels["total_sales"].configure(text=str(row[0]))
            self.kpi_labels["total_revenue"].configure(text=f"{row[1]:.0f} ₽")
            self.kpi_labels["avg_sale"].configure(text=f"{row[2]:.0f} ₽")
            
            # Товаров продано
            cursor = self.db.execute("""
                SELECT COALESCE(SUM(quantity), 0)
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE s.date >= ? AND s.status = 'completed'
            """, (start_date,))
            sold = cursor.fetchone()[0]
            self.kpi_labels["products_sold"].configure(text=str(sold))
            
            # Последние продажи
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)
            
            cursor = self.db.execute("""
                SELECT s.id, s.date, c.name, s.total_amount, s.status
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.date >= ?
                ORDER BY s.date DESC
                LIMIT 50
            """, (start_date,))
            
            for sale in cursor.fetchall():
                customer = sale[2] if sale[2] else "Розничный"
                self.sales_tree.insert("", "end", values=(
                    sale[0], sale[1][:10], customer, f"{sale[3]:.2f}", sale[4]
                ))
            
            logger.info(f"Отчёт обновлён за период {days} дней")
            
        except Exception as e:
            logger.error(f"Ошибка формирования отчёта: {e}")
