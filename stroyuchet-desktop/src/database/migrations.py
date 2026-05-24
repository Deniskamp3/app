"""
Модуль миграции данных из веб-версии
"""

import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseMigrations:
    """Класс для миграции данных из веб-версии"""
    
    def __init__(self, source_db_path: Optional[Path] = None):
        self.source_db_path = source_db_path
    
    def migrate_from_web(self, source_path: str, dest_path: str) -> bool:
        """
        Миграция базы данных из веб-версии
        
        Args:
            source_path: Путь к базе данных веб-версии
            dest_path: Путь к целевой базе данных
            
        Returns:
            True если миграция успешна
        """
        try:
            source = Path(source_path)
            dest = Path(dest_path)
            
            if not source.exists():
                logger.error(f"Исходная БД не найдена: {source}")
                return False
            
            # Копирование файла БД
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            
            logger.info(f"Миграция выполнена: {source} -> {dest}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка миграции: {e}")
            return False
    
    def convert_passwords(self, db_connection):
        """
        Конвертация паролей из старого формата в bcrypt
        
        Args:
            db_connection: Подключение к базе данных
        """
        try:
            cursor = db_connection.execute("SELECT id, password_hash FROM users")
            users = cursor.fetchall()
            
            for user in users:
                # Проверка формата хеша
                password_hash = user['password_hash']
                
                # Если это не bcrypt хеш (не начинается с $2b$)
                if not password_hash.startswith('$2b$'):
                    # Требуется конвертация (реализуется при необходимости)
                    logger.info(f"Требуется конвертация пароля для пользователя {user['id']}")
            
            db_connection.commit()
            logger.info("Проверка паролей завершена")
            
        except Exception as e:
            logger.error(f"Ошибка конвертации паролей: {e}")
    
    def export_to_sql(self, db_connection, output_path: str) -> bool:
        """
        Экспорт базы данных в SQL файл
        
        Args:
            db_connection: Подключение к базе данных
            output_path: Путь для сохранения SQL файла
            
        Returns:
            True если экспорт успешен
        """
        try:
            tables = db_connection.get_table_names()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for table in tables:
                    if table == 'sqlite_sequence':
                        continue
                    
                    # Экспорт структуры
                    cursor = db_connection.execute(
                        f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)
                    )
                    row = cursor.fetchone()
                    if row and row[0]:
                        f.write(f"-- Таблица: {table}\n")
                        f.write(f"{row[0]};\n\n")
                    
                    # Экспорт данных
                    cursor = db_connection.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    if rows:
                        columns = [description[0] for description in cursor.description]
                        for row in rows:
                            values = []
                            for val in row:
                                if val is None:
                                    values.append('NULL')
                                elif isinstance(val, str):
                                    escaped = val.replace("'", "''")
                                    values.append(f"'{escaped}'")
                                else:
                                    values.append(str(val))
                            
                            f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
                        
                        f.write("\n")
            
            logger.info(f"Экспорт в SQL выполнен: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в SQL: {e}")
            return False
    
    def import_from_sql(self, db_connection, sql_path: str) -> bool:
        """
        Импорт базы данных из SQL файла
        
        Args:
            db_connection: Подключение к базе данных
            sql_path: Путь к SQL файлу
            
        Returns:
            True если импорт успешен
        """
        try:
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # Разделение на отдельные команды
            commands = sql_script.split(';')
            
            for command in commands:
                command = command.strip()
                if command and not command.startswith('--'):
                    db_connection.execute(command)
            
            db_connection.commit()
            logger.info(f"Импорт из SQL выполнен: {sql_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка импорта из SQL: {e}")
            db_connection.rollback()
            return False
