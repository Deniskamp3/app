"""
Модуль настройки логирования
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(log_dir: Optional[Path] = None, 
                  level: int = logging.INFO,
                  max_bytes: int = 10*1024*1024,  # 10 MB
                  backup_count: int = 5) -> logging.Logger:
    """
    Настройка системы логирования приложения
    
    Args:
        log_dir: Директория для логов
        level: Уровень логирования
        max_bytes: Максимальный размер файла лога
        backup_count: Количество резервных файлов
        
    Returns:
        Настроенный logger
    """
    if log_dir is None:
        log_dir = Path.cwd() / 'data' / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Создание основного logger
    logger = logging.getLogger('stroyuchet')
    logger.setLevel(level)
    
    # Очистка существующих handlers
    logger.handlers.clear()
    
    # Формат сообщений
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (для отладки)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler для общих логов
    app_log_file = log_dir / 'app.log'
    file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # File handler для ошибок
    error_log_file = log_dir / 'errors.log'
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    logger.info("Система логирования инициализирована")
    
    return logger
