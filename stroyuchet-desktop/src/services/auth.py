"""
Сервис аутентификации и авторизации пользователей
"""

import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис управления аутентификацией"""
    
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def authenticate(self, username: str, password: str) -> Dict:
        """
        Аутентификация пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            
        Returns:
            Dict с ключами: success, user, message
        """
        try:
            # Проверка блокировки
            lock_status = self._check_lockout(username)
            if not lock_status['allowed']:
                return {
                    'success': False,
                    'user': None,
                    'message': f"Аккаунт заблокирован до {lock_status['until']}"
                }
            
            # Поиск пользователя
            cursor = self.db.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1",
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                self._increment_failed_attempts(username)
                return {
                    'success': False,
                    'user': None,
                    'message': "Неверный логин или пароль"
                }
            
            # Проверка пароля
            if not self._verify_password(password, user['password_hash']):
                self._increment_failed_attempts(user['id'])
                return {
                    'success': False,
                    'user': None,
                    'message': "Неверный логин или пароль"
                }
            
            # Сброс попыток при успешном входе
            self._reset_failed_attempts(user['id'])
            
            # Логирование входа
            self._log_login(user['id'], True)
            
            return {
                'success': True,
                'user': dict(user),
                'message': "Вход выполнен успешно"
            }
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            return {
                'success': False,
                'user': None,
                'message': "Ошибка системы аутентификации"
            }
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Проверка пароля"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Ошибка проверки пароля: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _check_lockout(self, username: str) -> Dict:
        """Проверка блокировки аккаунта"""
        cursor = self.db.execute(
            "SELECT locked_until FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        
        if not row or not row['locked_until']:
            return {'allowed': True, 'until': None}
        
        locked_until = datetime.fromisoformat(row['locked_until'])
        if datetime.now() < locked_until:
            return {
                'allowed': False,
                'until': locked_until.strftime('%d.%m.%Y %H:%M')
            }
        
        # Блокировка истекла
        return {'allowed': True, 'until': None}
    
    def _increment_failed_attempts(self, user_id: int):
        """Увеличение счётчика неудачных попыток"""
        try:
            # Получение текущего количества попыток
            cursor = self.db.execute(
                "SELECT failed_attempts FROM users WHERE id = ?",
                (user_id if isinstance(user_id, int) else self._get_user_id(user_id),)
            )
            row = cursor.fetchone()
            
            if row:
                new_attempts = row['failed_attempts'] + 1
                
                if new_attempts >= self.MAX_FAILED_ATTEMPTS:
                    # Блокировка аккаунта
                    locked_until = datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                    self.db.execute(
                        """UPDATE users 
                           SET failed_attempts = ?, locked_until = ?
                           WHERE id = ?""",
                        (new_attempts, locked_until.isoformat(), user_id if isinstance(user_id, int) else self._get_user_id(user_id))
                    )
                    logger.warning(f"Аккаунт {user_id} заблокирован на {self.LOCKOUT_DURATION_MINUTES} минут")
                else:
                    self.db.execute(
                        "UPDATE users SET failed_attempts = ? WHERE id = ?",
                        (new_attempts, user_id if isinstance(user_id, int) else self._get_user_id(user_id))
                    )
                
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Ошибка увеличения счётчика попыток: {e}")
    
    def _get_user_id(self, username: str) -> Optional[int]:
        """Получение ID пользователя по имени"""
        cursor = self.db.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        return row['id'] if row else None
    
    def _reset_failed_attempts(self, user_id: int):
        """Сброс счётчика неудачных попыток"""
        self.db.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
            (user_id,)
        )
        self.db.commit()
    
    def _log_login(self, user_id: int, success: bool):
        """Логирование попытки входа"""
        try:
            self.db.execute(
                """INSERT INTO audit_log (user_id, action, entity_type, details)
                   VALUES (?, ?, ?, ?)""",
                (user_id, 'login' if success else 'login_failed', 'users', 
                 f"{'Успешный вход' if success else 'Неудачная попытка'}")
            )
            self.db.commit()
        except Exception as e:
            logger.error(f"Ошибка логирования входа: {e}")
    
    def create_user(self, username: str, password: str, full_name: str, 
                    role: str = 'seller') -> Dict:
        """
        Создание нового пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            full_name: Полное имя
            role: Роль (admin, manager, seller)
            
        Returns:
            Dict с результатом операции
        """
        try:
            password_hash = self.hash_password(password)
            
            self.db.execute(
                """INSERT INTO users (username, password_hash, full_name, role)
                   VALUES (?, ?, ?, ?)""",
                (username, password_hash, full_name, role)
            )
            self.db.commit()
            
            logger.info(f"Создан пользователь: {username}")
            return {
                'success': True,
                'message': f"Пользователь {username} создан"
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def change_password(self, user_id: int, old_password: str, 
                       new_password: str) -> Dict:
        """
        Смена пароля пользователя
        
        Args:
            user_id: ID пользователя
            old_password: Старый пароль
            new_password: Новый пароль
            
        Returns:
            Dict с результатом операции
        """
        try:
            # Проверка старого пароля
            cursor = self.db.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user or not self._verify_password(old_password, user['password_hash']):
                return {
                    'success': False,
                    'message': "Неверный текущий пароль"
                }
            
            # Установка нового пароля
            new_hash = self.hash_password(new_password)
            self.db.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_hash, user_id)
            )
            self.db.commit()
            
            logger.info(f"Пароль изменён для пользователя {user_id}")
            return {
                'success': True,
                'message': "Пароль успешно изменён"
            }
            
        except Exception as e:
            logger.error(f"Ошибка смены пароля: {e}")
            return {
                'success': False,
                'message': str(e)
            }
