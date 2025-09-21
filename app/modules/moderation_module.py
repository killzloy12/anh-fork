#!/usr/bin/env python3
"""
🛡️ MODERATION MODULE v2.0
Модуль автоматической модерации и контроля
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class ModerationModule:
    """🛡️ Модуль модерации"""
    
    def __init__(self, db_service, config):
        self.db = db_service
        self.config = config
        
        # Словарь запрещенных слов
        self.banned_words = [
            'спам', 'реклама', 'мошенник', 'обман'
        ]
        
        # Паттерны спама
        self.spam_patterns = [
            r'(https?://\S+){3,}',  # Множественные ссылки
            r'(.)\1{10,}',  # Повторяющиеся символы
            r'[A-Z]{20,}'   # Много заглавных букв
        ]
        
        # Счетчики для пользователей
        self.user_warnings = {}
        self.flood_protection = {}
        
        logger.info("🛡️ Moderation Module инициализирован")
    
    async def check_message(self, user_id: int, chat_id: int, message: str) -> Dict[str, Any]:
        """🔍 Проверка сообщения"""
        
        try:
            checks = {
                'is_spam': self._check_spam(message),
                'has_banned_words': self._check_banned_words(message),
                'is_flood': self._check_flood(user_id),
                'toxicity_level': self._check_toxicity(message)
            }
            
            # Определяем действие
            action = 'allow'
            reason = ''
            
            if checks['is_spam']:
                action = 'delete'
                reason = 'Спам'
            elif checks['has_banned_words']:
                action = 'warn'
                reason = 'Запрещенные слова'
            elif checks['is_flood']:
                action = 'timeout'
                reason = 'Флуд'
            elif checks['toxicity_level'] > self.config.moderation.toxicity_threshold:
                action = 'warn'
                reason = 'Токсичность'
            
            # Записываем действие
            if action != 'allow':
                await self._log_moderation_action(user_id, chat_id, action, reason)
            
            return {
                'action': action,
                'reason': reason,
                'checks': checks,
                'user_warnings': self.user_warnings.get(user_id, 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки сообщения: {e}")
            return {'action': 'allow', 'error': str(e)}
    
    def _check_spam(self, message: str) -> bool:
        """📧 Проверка на спам"""
        
        try:
            for pattern in self.spam_patterns:
                if re.search(pattern, message):
                    return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки спама: {e}")
            return False
    
    def _check_banned_words(self, message: str) -> bool:
        """🚫 Проверка запрещенных слов"""
        
        message_lower = message.lower()
        return any(word in message_lower for word in self.banned_words)
    
    def _check_flood(self, user_id: int) -> bool:
        """🌊 Проверка флуда"""
        
        try:
            current_time = datetime.now()
            
            if user_id not in self.flood_protection:
                self.flood_protection[user_id] = []
            
            # Добавляем текущее время
            self.flood_protection[user_id].append(current_time)
            
            # Оставляем только последние сообщения за минуту
            minute_ago = current_time - timedelta(minutes=1)
            self.flood_protection[user_id] = [
                t for t in self.flood_protection[user_id] 
                if t > minute_ago
            ]
            
            # Проверяем количество сообщений
            return len(self.flood_protection[user_id]) > self.config.moderation.flood_threshold
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки флуда: {e}")
            return False
    
    def _check_toxicity(self, message: str) -> float:
        """☠️ Проверка токсичности"""
        
        try:
            # Простая проверка токсичности
            toxic_words = ['дурак', 'идиот', 'тупой', 'глупый']
            toxic_count = sum(1 for word in toxic_words if word in message.lower())
            
            # Нормализуем от 0 до 1
            return min(1.0, toxic_count / 3)
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки токсичности: {e}")
            return 0.0
    
    async def _log_moderation_action(self, user_id: int, chat_id: int, action: str, reason: str):
        """📝 Логирование действий модерации"""
        
        try:
            # Сохраняем в БД
            await self.db.track_event(
                user_id, chat_id, 'moderation_action',
                {'action': action, 'reason': reason}
            )
            
            # Увеличиваем счетчик предупреждений
            if action == 'warn':
                self.user_warnings[user_id] = self.user_warnings.get(user_id, 0) + 1
            
            logger.info(f"🛡️ Модерация: {action} для пользователя {user_id}, причина: {reason}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка логирования модерации: {e}")
    
    def get_user_warnings(self, user_id: int) -> int:
        """⚠️ Получение количества предупреждений"""
        return self.user_warnings.get(user_id, 0)
    
    def reset_user_warnings(self, user_id: int) -> bool:
        """🔄 Сброс предупреждений"""
        
        try:
            if user_id in self.user_warnings:
                del self.user_warnings[user_id]
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сброса предупреждений: {e}")
            return False


__all__ = ["ModerationModule"]