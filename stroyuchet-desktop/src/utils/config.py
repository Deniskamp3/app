"""
Модуль управления конфигурацией приложения
"""

import configparser
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Менеджер конфигурации приложения (INI-файлы)"""
    
    DEFAULT_CONFIG = {
        'app': {
            'name': 'СтройУчёт',
            'version': '1.0.0',
            'theme': 'system',
            'language': 'ru'
        },
        'database': {
            'auto_backup': 'True',
            'backup_time': '00:00'
        },
        'company': {
            'name': 'ООО "СтройУчёт"',
            'inn': '',
            'address': '',
            'phone': ''
        },
        'receipt': {
            'header': 'Чек',
            'footer': 'Спасибо за покупку!'
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.cwd() / 'data' / 'config.ini'
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.config = configparser.ConfigParser()
        self._load_or_create()
    
    def _load_or_create(self):
        """Загрузка существующей конфигурации или создание новой"""
        if self.config_path.exists():
            self.config.read(self.config_path, encoding='utf-8')
            logger.info(f"Конфигурация загружена: {self.config_path}")
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Создание конфигурации по умолчанию"""
        for section, options in self.DEFAULT_CONFIG.items():
            self.config.add_section(section)
            for key, value in options.items():
                self.config.set(section, key, str(value))
        
        self._save()
        logger.info(f"Создана конфигурация по умолчанию: {self.config_path}")
    
    def _save(self):
        """Сохранение конфигурации"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        Получение значения из конфигурации
        
        Args:
            section: Секция конфигурации
            key: Ключ
            fallback: Значение по умолчанию
            
        Returns:
            Значение конфигурации
        """
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Получение целочисленного значения"""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Получение булевого значения"""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def set(self, section: str, key: str, value: Any):
        """
        Установка значения в конфигурации
        
        Args:
            section: Секция конфигурации
            key: Ключ
            value: Значение
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, str(value))
        self._save()
    
    def remove(self, section: str, key: str) -> bool:
        """
        Удаление значения из конфигурации
        
        Args:
            section: Секция конфигурации
            key: Ключ
            
        Returns:
            True если успешно
        """
        try:
            self.config.remove_option(section, key)
            self._save()
            return True
        except configparser.NoSectionError:
            return False
    
    def get_all(self, section: str) -> dict:
        """
        Получение всех значений секции
        
        Args:
            section: Секция конфигурации
            
        Returns:
            Dict со значениями
        """
        try:
            return dict(self.config.items(section))
        except configparser.NoSectionError:
            return {}
    
    def reload(self):
        """Перезагрузка конфигурации из файла"""
        self.config.clear()
        self._load_or_create()
    
    def reset_to_defaults(self):
        """Сброс к конфигурации по умолчанию"""
        self.config.clear()
        self._create_default_config()
