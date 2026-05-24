"""
Сервис продаж
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SalesService:
    """Сервис управления продажами"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_sale(self, customer_id: Optional[int], items: List[Dict], 
                    user_id: int, payment_method: str = 'cash',
                    discount: float = 0, notes: str = '') -> Dict:
        """
        Оформление продажи
        
        Args:
            customer_id: ID клиента (опционально)
            items: Список товаров [{'product_id': 1, 'quantity': 2, 'price': 100}]
            user_id: ID пользователя
            payment_method: Способ оплаты (cash, card, transfer)
            discount: Скидка в процентах
            notes: Примечание
            
        Returns:
            Dict с результатом операции
        """
        try:
            # Генерация номера продажи
            sale_number = self._generate_sale_number()
            
            # Расчёт суммы
            total_amount = sum(item['quantity'] * item['price'] for item in items)
            final_amount = total_amount * (1 - discount / 100)
            
            # Создание записи о продаже
            self.db.execute(
                """INSERT INTO sales 
                   (sale_number, customer_id, user_id, total_amount, discount, 
                    final_amount, payment_method, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (sale_number, customer_id, user_id, total_amount, discount, 
                 final_amount, payment_method, notes)
            )
            
            sale_id = self.db.connection.lastrowid
            
            # Добавление позиций
            for item in items:
                product = self._get_product(item['product_id'])
                
                self.db.execute(
                    """INSERT INTO sale_items 
                       (sale_id, product_id, product_name, product_sku, 
                        quantity, price, discount, total)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (sale_id, item['product_id'], product['name'], product['sku'],
                     item['quantity'], item['price'], item.get('discount', 0),
                     item['quantity'] * item['price'] * (1 - item.get('discount', 0) / 100))
                )
                
                # Обновление остатков
                self._update_product_quantity(item['product_id'], -item['quantity'])
            
            self.db.commit()
            
            # Логирование
            self._log_action(user_id, 'sale_created', 'sales', sale_id, 
                           f"Создана продажа {sale_number}")
            
            logger.info(f"Создана продажа {sale_number} на сумму {final_amount}")
            
            return {
                'success': True,
                'sale_id': sale_id,
                'sale_number': sale_number,
                'total': final_amount,
                'message': f"Продажа {sale_number} оформлена"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания продажи: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def _generate_sale_number(self) -> str:
        """Генерация уникального номера продажи"""
        date_str = datetime.now().strftime('%Y%m%d')
        
        cursor = self.db.execute(
            """SELECT COUNT(*) as count FROM sales 
               WHERE sale_number LIKE ?""",
            (f'SAL-{date_str}-%',)
        )
        count = cursor.fetchone()['count'] + 1
        
        return f"SAL-{date_str}-{count:04d}"
    
    def _get_product(self, product_id: int) -> Dict:
        """Получение информации о товаре"""
        cursor = self.db.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else {}
    
    def _update_product_quantity(self, product_id: int, quantity_change: float):
        """Обновление количества товара на складе"""
        self.db.execute(
            """UPDATE products 
               SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (quantity_change, product_id)
        )
    
    def _log_action(self, user_id: int, action: str, entity_type: str, 
                    entity_id: int, details: str):
        """Логирование действия"""
        self.db.execute(
            """INSERT INTO audit_log 
               (user_id, action, entity_type, entity_id, details)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, action, entity_type, entity_id, details)
        )
    
    def get_sales(self, date_from: Optional[str] = None, 
                  date_to: Optional[str] = None,
                  customer_id: Optional[int] = None,
                  status: Optional[str] = None,
                  limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Получение списка продаж с фильтрацией
        
        Args:
            date_from: Дата от (YYYY-MM-DD)
            date_to: Дата до (YYYY-MM-DD)
            customer_id: ID клиента
            status: Статус продажи
            limit: Лимит записей
            offset: Смещение
            
        Returns:
            Список продаж
        """
        query = """
            SELECT s.*, u.full_name as user_name, c.name as customer_name
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE 1=1
        """
        params = []
        
        if date_from:
            query += " AND DATE(s.created_at) >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(s.created_at) <= ?"
            params.append(date_to)
        
        if customer_id:
            query += " AND s.customer_id = ?"
            params.append(customer_id)
        
        if status:
            query += " AND s.status = ?"
            params.append(status)
        
        query += " ORDER BY s.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = self.db.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sale_items(self, sale_id: int) -> List[Dict]:
        """Получение позиций продажи"""
        cursor = self.db.execute(
            "SELECT * FROM sale_items WHERE sale_id = ?",
            (sale_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def refund_sale(self, sale_id: int, user_id: int, reason: str = '') -> Dict:
        """
        Возврат продажи
        
        Args:
            sale_id: ID продажи
            user_id: ID пользователя
            reason: Причина возврата
            
        Returns:
            Dict с результатом операции
        """
        try:
            # Проверка статуса
            cursor = self.db.execute(
                "SELECT status FROM sales WHERE id = ?",
                (sale_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return {'success': False, 'message': 'Продажа не найдена'}
            
            if row['status'] != 'completed':
                return {'success': False, 'message': 'Нельзя вернуть продажу с таким статусом'}
            
            # Обновление статуса
            self.db.execute(
                """UPDATE sales 
                   SET status = 'refunded', updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (sale_id,)
            )
            
            # Возврат товаров на склад
            items = self.get_sale_items(sale_id)
            for item in items:
                self._update_product_quantity(item['product_id'], item['quantity'])
            
            self.db.commit()
            
            # Логирование
            self._log_action(user_id, 'sale_refunded', 'sales', sale_id,
                           f"Возврат продажи. Причина: {reason}")
            
            logger.info(f"Выполнен возврат продажи {sale_id}")
            
            return {
                'success': True,
                'message': 'Возврат выполнен успешно'
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка возврата: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict:
        """
        Получение статистики продаж за день
        
        Args:
            date: Дата (YYYY-MM-DD), по умолчанию сегодня
            
        Returns:
            Dict со статистикой
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        cursor = self.db.execute(
            """SELECT 
                   COUNT(*) as total_sales,
                   SUM(final_amount) as total_revenue,
                   AVG(final_amount) as avg_sale
               FROM sales
               WHERE DATE(created_at) = ? AND status = 'completed'""",
            (date,)
        )
        row = cursor.fetchone()
        
        return {
            'date': date,
            'total_sales': row['total_sales'] or 0,
            'total_revenue': row['total_revenue'] or 0,
            'avg_sale': row['avg_sale'] or 0
        }
