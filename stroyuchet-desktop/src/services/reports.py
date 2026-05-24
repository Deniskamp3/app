"""
Сервис отчётов и экспорта
"""

from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ReportsService:
    """Сервис генерации отчётов и экспорта данных"""
    
    def __init__(self, db_connection, export_dir: Optional[Path] = None):
        self.db = db_connection
        self.export_dir = export_dir or Path.cwd() / 'data' / 'exports'
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def get_sales_report(self, date_from: str, date_to: str, 
                         group_by: str = 'day') -> List[Dict]:
        """
        Отчёт по продажам за период
        
        Args:
            date_from: Дата начала (YYYY-MM-DD)
            date_to: Дата окончания (YYYY-MM-DD)
            group_by: Группировка (day, week, month)
            
        Returns:
            Список записей отчёта
        """
        if group_by == 'day':
            date_format = '%Y-%m-%d'
        elif group_by == 'month':
            date_format = '%Y-%m'
        else:
            date_format = '%Y-%W'  # неделя
        
        query = f"""
            SELECT 
                DATE(created_at) as period,
                COUNT(*) as total_sales,
                SUM(final_amount) as total_revenue,
                AVG(final_amount) as avg_sale
            FROM sales
            WHERE DATE(created_at) BETWEEN ? AND ?
              AND status = 'completed'
            GROUP BY strftime('{date_format}', created_at)
            ORDER BY period
        """
        
        cursor = self.db.execute(query, (date_from, date_to))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_products_report(self, category_id: Optional[int] = None) -> List[Dict]:
        """
        Отчёт по товарам
        
        Args:
            category_id: ID категории (опционально)
            
        Returns:
            Список товаров
        """
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
        """
        params = []
        
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        
        query += " ORDER BY p.name"
        
        cursor = self.db.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_low_stock_products(self, threshold: int = 10) -> List[Dict]:
        """
        Отчёт по товарам с низким остатком
        
        Args:
            threshold: Порог остатка
            
        Returns:
            Список товаров
        """
        cursor = self.db.execute(
            """SELECT * FROM products 
               WHERE quantity <= min_quantity AND is_active = 1
               ORDER BY quantity ASC""",
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def export_to_excel(self, data: List[Dict], filename: str, 
                        sheet_name: str = 'Sheet1') -> Dict:
        """
        Экспорт данных в Excel
        
        Args:
            data: Данные для экспорта (список словарей)
            filename: Имя файла
            sheet_name: Название листа
            
        Returns:
            Dict с результатом операции
        """
        try:
            from openpyxl import Workbook
            
            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name
            
            if not data:
                raise ValueError("Нет данных для экспорта")
            
            # Заголовки
            headers = list(data[0].keys())
            ws.append(headers)
            
            # Данные
            for row in data:
                ws.append([row.get(h, '') for h in headers])
            
            # Автоширина колонок
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column].width = adjusted_width
            
            # Сохранение
            filepath = self.export_dir / filename
            wb.save(str(filepath))
            
            logger.info(f"Экспорт в Excel: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'message': f'Файл сохранён: {filepath}'
            }
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def export_to_pdf(self, data: List[Dict], filename: str, 
                      title: str = 'Отчёт') -> Dict:
        """
        Экспорт данных в PDF
        
        Args:
            data: Данные для экспорта
            filename: Имя файла
            title: Заголовок отчёта
            
        Returns:
            Dict с результатом операции
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.enums import TA_CENTER
            
            filepath = self.export_dir / filename
            
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=landscape(A4),
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # Заголовок
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=20
            )
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Таблица
            if data:
                headers = list(data[0].keys())
                table_data = [headers]
                
                for row in data:
                    table_data.append([str(row.get(h, '')) for h in headers])
                
                table = Table(table_data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ]))
                
                elements.append(table)
            
            doc.build(elements)
            
            logger.info(f"Экспорт в PDF: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'message': f'Файл сохранён: {filepath}'
            }
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в PDF: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_dashboard_stats(self) -> Dict:
        """
        Статистика для панели управления
        
        Returns:
            Dict со статистикой
        """
        stats = {}
        
        # Всего продаж сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        cursor = self.db.execute(
            """SELECT COUNT(*) as count, SUM(final_amount) as total
               FROM sales
               WHERE DATE(created_at) = ? AND status = 'completed'""",
            (today,)
        )
        row = cursor.fetchone()
        stats['today_sales'] = row['count'] or 0
        stats['today_revenue'] = row['total'] or 0
        
        # Всего продаж за месяц
        month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        cursor = self.db.execute(
            """SELECT COUNT(*) as count, SUM(final_amount) as total
               FROM sales
               WHERE DATE(created_at) >= ? AND status = 'completed'""",
            (month_start,)
        )
        row = cursor.fetchone()
        stats['month_sales'] = row['count'] or 0
        stats['month_revenue'] = row['total'] or 0
        
        # Товаров на складе
        cursor = self.db.execute(
            "SELECT COUNT(*) as count FROM products WHERE is_active = 1"
        )
        stats['total_products'] = cursor.fetchone()['count'] or 0
        
        # Товаров с низким остатком
        cursor = self.db.execute(
            """SELECT COUNT(*) as count FROM products 
               WHERE quantity <= min_quantity AND is_active = 1"""
        )
        stats['low_stock'] = cursor.fetchone()['count'] or 0
        
        # Всего клиентов
        cursor = self.db.execute(
            "SELECT COUNT(*) as count FROM customers WHERE is_active = 1"
        )
        stats['total_customers'] = cursor.fetchone()['count'] or 0
        
        return stats
