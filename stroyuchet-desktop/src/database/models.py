"""
Модуль моделей базы данных и создания таблиц
"""

import sqlite3
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseModels:
    """Класс для создания и управления таблицами базы данных"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_all_tables(self):
        """Создание всех таблиц базы данных"""
        self._create_users_table()
        self._create_categories_table()
        self._create_products_table()
        self._create_customers_table()
        self._create_sales_table()
        self._create_sale_items_table()
        self._create_supplies_table()
        self._create_app_settings_table()
        self._create_audit_log_table()
        self._create_backups_table()
        self._create_default_data()
        logger.info("Все таблицы созданы успешно")
    
    def _create_users_table(self):
        """Таблица пользователей"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'seller')),
                is_active BOOLEAN DEFAULT 1,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        self.db.commit()
    
    def _create_categories_table(self):
        """Таблица категорий товаров"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER REFERENCES categories(id),
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id)")
        self.db.commit()
    
    def _create_products_table(self):
        """Таблица товаров"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                unit TEXT NOT NULL DEFAULT 'шт',
                price_buy REAL NOT NULL DEFAULT 0,
                price_sell REAL NOT NULL DEFAULT 0,
                quantity REAL NOT NULL DEFAULT 0,
                min_quantity REAL NOT NULL DEFAULT 10,
                supplier TEXT,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
        self.db.commit()
    
    def _create_customers_table(self):
        """Таблица клиентов"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                inn TEXT,
                kpp TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                contact_person TEXT,
                discount REAL DEFAULT 0,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_customers_inn ON customers(inn)")
        self.db.commit()
    
    def _create_sales_table(self):
        """Таблица продаж"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER REFERENCES customers(id),
                user_id INTEGER REFERENCES users(id),
                total_amount REAL NOT NULL DEFAULT 0,
                discount REAL DEFAULT 0,
                final_amount REAL NOT NULL DEFAULT 0,
                payment_method TEXT DEFAULT 'cash' CHECK(payment_method IN ('cash', 'card', 'transfer')),
                status TEXT DEFAULT 'completed' CHECK(status IN ('completed', 'refunded', 'cancelled')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_sales_number ON sales(sale_number)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_sales_user ON sales(user_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_sales_created ON sales(created_at)")
        self.db.commit()
    
    def _create_sale_items_table(self):
        """Таблица позиций продаж"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id),
                product_name TEXT NOT NULL,
                product_sku TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                discount REAL DEFAULT 0,
                total REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id)")
        self.db.commit()
    
    def _create_supplies_table(self):
        """Таблица поставок"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS supplies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supply_number TEXT UNIQUE NOT NULL,
                supplier_name TEXT NOT NULL,
                document_number TEXT,
                document_date DATE,
                total_amount REAL NOT NULL DEFAULT 0,
                notes TEXT,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS supply_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supply_id INTEGER NOT NULL REFERENCES supplies(id) ON DELETE CASCADE,
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_supplies_number ON supplies(supply_number)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_supply_items_supply ON supply_items(supply_id)")
        self.db.commit()
    
    def _create_app_settings_table(self):
        """Таблица настроек приложения"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()
    
    def _create_audit_log_table(self):
        """Таблица журнала аудита"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at)")
        self.db.commit()
    
    def _create_backups_table(self):
        """Таблица резервных копий"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                size_bytes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_automatic BOOLEAN DEFAULT 1
            )
        """)
        self.db.commit()
    
    def _create_default_data(self):
        """Создание данных по умолчанию"""
        # Настройки по умолчанию
        settings = [
            ('company_name', 'ООО "СтройУчёт"'),
            ('company_inn', ''),
            ('company_address', ''),
            ('company_phone', ''),
            ('theme', 'system'),
            ('auto_backup', '1'),
            ('receipt_footer', 'Спасибо за покупку!'),
        ]
        
        for key, value in settings:
            try:
                self.db.execute(
                    "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
                    (key, value)
                )
            except sqlite3.IntegrityError:
                pass
        
        self.db.commit()
    
    def drop_all_tables(self):
        """Удаление всех таблиц (для тестирования)"""
        tables = self.db.get_table_names()
        for table in tables:
            if table != 'sqlite_sequence':
                self.db.execute(f"DROP TABLE IF EXISTS {table}")
        self.db.commit()
        logger.info("Все таблицы удалены")
