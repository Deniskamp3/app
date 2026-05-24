"""
Модуль подключения к базе данных SQLite
"""

import sqlite3
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Класс для управления подключением к базе данных SQLite"""
    
    _instance: Optional['DatabaseConnection'] = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls, db_path: Optional[Path] = None):
        """Реализация паттерна Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: Optional[Path] = None):
        """Инициализация подключения к БД"""
        if self._connection is not None:
            return
            
        self.db_path = db_path or Path.cwd() / 'data' / 'database.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connect()
        self._enable_wal_mode()
        self._check_integrity()
    
    def _connect(self):
        """Установка соединения с базой данных"""
        try:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._connection.row_factory = sqlite3.Row
            logger.info(f"Подключение к БД: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise
    
    def _enable_wal_mode(self):
        """Включение WAL-режима для параллельного чтения"""
        try:
            cursor = self._connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64 MB cache
            self._connection.commit()
            logger.info("WAL-режим включён")
        except sqlite3.Error as e:
            logger.warning(f"Не удалось включить WAL-режим: {e}")
    
    def _check_integrity(self):
        """Проверка целостности базы данных"""
        try:
            cursor = self._connection.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            if result != 'ok':
                logger.warning(f"Проблемы целостности БД: {result}")
            else:
                logger.info("Целостность БД подтверждена")
        except sqlite3.Error as e:
            logger.error(f"Ошибка проверки целостности: {e}")
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Получение активного соединения"""
        if self._connection is None:
            self._connect()
        return self._connection
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Выполнение SQL-запроса"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor
    
    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """Выполнение SQL-запроса с несколькими наборами параметров"""
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        return cursor
    
    def commit(self):
        """Фиксация транзакции"""
        if self._connection:
            self._connection.commit()
    
    def rollback(self):
        """Откат транзакции"""
        if self._connection:
            self._connection.rollback()
    
    def close(self):
        """Закрытие соединения"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Соединение с БД закрыто")
    
    def get_table_names(self) -> list:
        """Получение списка таблиц"""
        cursor = self.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]
