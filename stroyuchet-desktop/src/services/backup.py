"""
Сервис резервного копирования базы данных
"""

import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BackupService:
    """Сервис резервного копирования и восстановления БД"""
    
    MAX_BACKUPS = 30  # Хранить последние 30 бэкапов
    
    def __init__(self, db_path: Path, backup_dir: Optional[Path] = None):
        self.db_path = db_path
        self.backup_dir = backup_dir or db_path.parent / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, is_automatic: bool = False) -> Dict:
        """
        Создание резервной копии БД
        
        Args:
            is_automatic: Флаг автоматического бэкапа
            
        Returns:
            Dict с результатом операции
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            prefix = 'auto' if is_automatic else 'manual'
            filename = f"db_{prefix}_{timestamp}.db"
            backup_path = self.backup_dir / filename
            
            # Копирование файла БД
            shutil.copy2(self.db_path, backup_path)
            
            # Получение размера
            size_bytes = backup_path.stat().st_size
            
            logger.info(f"Создан бэкап: {filename} ({size_bytes} байт)")
            
            # Удаление старых бэкапов
            self._cleanup_old_backups()
            
            return {
                'success': True,
                'filename': filename,
                'filepath': str(backup_path),
                'size_bytes': size_bytes,
                'message': f'Бэкап создан: {filename}'
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания бэкапа: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def restore_backup(self, backup_filename: str) -> Dict:
        """
        Восстановление из резервной копии
        
        Args:
            backup_filename: Имя файла бэкапа
            
        Returns:
            Dict с результатом операции
        """
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'message': f'Файл бэкапа не найден: {backup_filename}'
                }
            
            # Создание бэкапа текущей БД перед восстановлением
            self.create_backup(is_automatic=False)
            
            # Восстановление
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"Восстановлено из бэкапа: {backup_filename}")
            
            return {
                'success': True,
                'message': f'Восстановлено из бэкапа: {backup_filename}'
            }
            
        except Exception as e:
            logger.error(f"Ошибка восстановления: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def list_backups(self) -> List[Dict]:
        """
        Получение списка бэкапов
        
        Returns:
            Список бэкапов
        """
        backups = []
        
        for filepath in self.backup_dir.glob('db_*.db'):
            stat = filepath.stat()
            backups.append({
                'filename': filepath.name,
                'size_bytes': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'is_automatic': 'auto' in filepath.name
            })
        
        # Сортировка по дате (новые сначала)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
    
    def delete_backup(self, filename: str) -> Dict:
        """
        Удаление бэкапа
        
        Args:
            filename: Имя файла бэкапа
            
        Returns:
            Dict с результатом операции
        """
        try:
            backup_path = self.backup_dir / filename
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'message': f'Файл не найден: {filename}'
                }
            
            backup_path.unlink()
            logger.info(f"Удалён бэкап: {filename}")
            
            return {
                'success': True,
                'message': f'Бэкап удалён: {filename}'
            }
            
        except Exception as e:
            logger.error(f"Ошибка удаления бэкапа: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def _cleanup_old_backups(self):
        """Удаление старых бэкапов, превышающих лимит"""
        try:
            backups = self.list_backups()
            
            if len(backups) > self.MAX_BACKUPS:
                # Удаление самых старых
                for backup in backups[self.MAX_BACKUPS:]:
                    self.delete_backup(backup['filename'])
                
                logger.info(f"Удалено {len(backups) - self.MAX_BACKUPS} старых бэкапов")
                
        except Exception as e:
            logger.error(f"Ошибка очистки старых бэкапов: {e}")
    
    def get_backup_stats(self) -> Dict:
        """
        Получение статистики бэкапов
        
        Returns:
            Dict со статистикой
        """
        backups = self.list_backups()
        
        total_size = sum(b['size_bytes'] for b in backups)
        auto_count = sum(1 for b in backups if b['is_automatic'])
        manual_count = len(backups) - auto_count
        
        last_backup = None
        if backups:
            last_backup = {
                'filename': backups[0]['filename'],
                'created_at': backups[0]['created_at']
            }
        
        return {
            'total_backups': len(backups),
            'automatic_backups': auto_count,
            'manual_backups': manual_count,
            'total_size_bytes': total_size,
            'last_backup': last_backup
        }
    
    def schedule_daily_backup(self):
        """
        Проверка необходимости ежедневного бэкапа
        
        Returns:
            True если бэкап был создан
        """
        stats = self.get_backup_stats()
        
        if not stats['last_backup']:
            # Нет бэкапов вообще
            return self.create_backup(is_automatic=True)['success']
        
        last_backup_date = datetime.fromisoformat(stats['last_backup']['created_at']).date()
        today = datetime.now().date()
        
        if last_backup_date < today:
            # Прошлая резервная копия старше сегодня
            return self.create_backup(is_automatic=True)['success']
        
        return False
