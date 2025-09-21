#!/usr/bin/env python3
"""
🔒 PERMISSIONS MODULE v3.0 - ИСПРАВЛЕНО
🛡️ Система ограничений и разрешений доступа

Контроль доступа к функциям бота по чатам, пользователям и командам
"""

import logging
import json
import asyncio  # ДОБАВЛЕН ИМПОРТ
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class PermissionsModule:
    """🔒 Модуль управления разрешениями"""
    
    def __init__(self, config):
        self.config = config
        
        # Файл с настройками доступа
        self.permissions_file = Path('data/permissions.json')
        
        # Разрешенные чаты (whitelist)
        self.allowed_chats: Set[int] = set()
        
        # Заблокированные чаты (blacklist)
        self.blocked_chats: Set[int] = set()
        
        # Разрешенные пользователи
        self.allowed_users: Set[int] = set()
        
        # Заблокированные пользователи
        self.blocked_users: Set[int] = set()
        
        # Ограничения команд по чатам
        self.command_restrictions: Dict[str, Set[int]] = {}
        
        # Настройки модулей по чатам
        self.module_settings: Dict[int, Dict[str, bool]] = {}
        
        # Настройки по умолчанию
        self.default_settings = {
            'ai_enabled': True,
            'crypto_enabled': True,
            'analytics_enabled': True,
            'moderation_enabled': True,
            'triggers_enabled': True,
            'stickers_enabled': True,
            'charts_enabled': True
        }
        
        logger.info("🔒 Permissions Module инициализирован")
    
    async def initialize(self):
        """📥 Отложенная инициализация разрешений"""
        await self.load_permissions()
    
    async def load_permissions(self):
        """📥 Загрузка настроек разрешений"""
        
        try:
            if self.permissions_file.exists():
                with open(self.permissions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Загружаем списки доступа
                    self.allowed_chats = set(data.get('allowed_chats', []))
                    self.blocked_chats = set(data.get('blocked_chats', []))
                    self.allowed_users = set(data.get('allowed_users', []))
                    self.blocked_users = set(data.get('blocked_users', []))
                    
                    # Загружаем ограничения команд
                    cmd_restrictions = data.get('command_restrictions', {})
                    self.command_restrictions = {
                        cmd: set(chats) for cmd, chats in cmd_restrictions.items()
                    }
                    
                    # Загружаем настройки модулей
                    self.module_settings = {
                        int(chat_id): settings 
                        for chat_id, settings in data.get('module_settings', {}).items()
                    }
                
                logger.info("📥 Настройки разрешений загружены")
            else:
                logger.info("📝 Создаем файл разрешений по умолчанию")
                await self.save_permissions()
                
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки разрешений: {e}")
    
    async def save_permissions(self):
        """💾 Сохранение настроек разрешений"""
        
        try:
            data = {
                'allowed_chats': list(self.allowed_chats),
                'blocked_chats': list(self.blocked_chats),
                'allowed_users': list(self.allowed_users),
                'blocked_users': list(self.blocked_users),
                'command_restrictions': {
                    cmd: list(chats) for cmd, chats in self.command_restrictions.items()
                },
                'module_settings': {
                    str(chat_id): settings 
                    for chat_id, settings in self.module_settings.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            
            self.permissions_file.parent.mkdir(exist_ok=True)
            
            with open(self.permissions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Настройки разрешений сохранены")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения разрешений: {e}")
            return False
    
    async def check_chat_access(self, chat_id: int, user_id: int = None) -> bool:
        """🔍 Проверка доступа к чату"""
        
        try:
            # Админы могут все
            if user_id and user_id in self.config.bot.admin_ids:
                return True
            
            # Проверяем заблокированные чаты
            if chat_id in self.blocked_chats:
                return False
            
            # Проверяем заблокированных пользователей
            if user_id and user_id in self.blocked_users:
                return False
            
            # Если есть whitelist чатов, проверяем его
            if self.allowed_chats:
                if chat_id not in self.allowed_chats:
                    return False
            
            # Если есть whitelist пользователей, проверяем его
            if self.allowed_users:
                if not user_id or user_id not in self.allowed_users:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступа к чату: {e}")
            return True  # В случае ошибки разрешаем доступ
    
    async def check_command_access(self, command: str, chat_id: int, user_id: int = None) -> bool:
        """⚡ Проверка доступа к команде"""
        
        try:
            # Сначала проверяем базовый доступ к чату
            if not await self.check_chat_access(chat_id, user_id):
                return False
            
            # Админы могут использовать любые команды
            if user_id and user_id in self.config.bot.admin_ids:
                return True
            
            # Проверяем ограничения команды
            if command in self.command_restrictions:
                allowed_chats = self.command_restrictions[command]
                if allowed_chats and chat_id not in allowed_chats:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступа к команде: {e}")
            return True
    
    async def check_module_access(self, module_name: str, chat_id: int, user_id: int = None) -> bool:
        """🧩 Проверка доступа к модулю"""
        
        try:
            # Проверяем базовый доступ
            if not await self.check_chat_access(chat_id, user_id):
                return False
            
            # Админы могут использовать любые модули
            if user_id and user_id in self.config.bot.admin_ids:
                return True
            
            # Получаем настройки для чата
            chat_settings = self.module_settings.get(chat_id, self.default_settings)
            
            # Проверяем доступ к модулю
            setting_key = f"{module_name}_enabled"
            return chat_settings.get(setting_key, True)
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступа к модулю: {e}")
            return True
    
    async def add_allowed_chat(self, chat_id: int, user_id: int = None) -> bool:
        """➕ Добавление чата в whitelist"""
        
        try:
            # Проверяем права
            if user_id and user_id not in self.config.bot.admin_ids:
                return False
            
            self.allowed_chats.add(chat_id)
            
            # Убираем из blacklist если есть
            self.blocked_chats.discard(chat_id)
            
            await self.save_permissions()
            
            logger.info(f"➕ Чат {chat_id} добавлен в whitelist")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления чата в whitelist: {e}")
            return False
    
    async def add_blocked_chat(self, chat_id: int, user_id: int = None) -> bool:
        """🚫 Добавление чата в blacklist"""
        
        try:
            # Проверяем права
            if user_id and user_id not in self.config.bot.admin_ids:
                return False
            
            self.blocked_chats.add(chat_id)
            
            # Убираем из whitelist если есть
            self.allowed_chats.discard(chat_id)
            
            await self.save_permissions()
            
            logger.info(f"🚫 Чат {chat_id} добавлен в blacklist")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления чата в blacklist: {e}")
            return False
    
    async def remove_chat_restriction(self, chat_id: int, user_id: int = None) -> bool:
        """🔓 Удаление ограничений чата"""
        
        try:
            # Проверяем права
            if user_id and user_id not in self.config.bot.admin_ids:
                return False
            
            self.allowed_chats.discard(chat_id)
            self.blocked_chats.discard(chat_id)
            
            await self.save_permissions()
            
            logger.info(f"🔓 Ограничения для чата {chat_id} сняты")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка снятия ограничений: {e}")
            return False
    
    async def set_module_setting(self, chat_id: int, module_name: str, 
                                enabled: bool, user_id: int = None) -> bool:
        """⚙️ Настройка модуля для чата"""
        
        try:
            # Проверяем права
            if user_id and user_id not in self.config.bot.admin_ids:
                return False
            
            if chat_id not in self.module_settings:
                self.module_settings[chat_id] = self.default_settings.copy()
            
            setting_key = f"{module_name}_enabled"
            self.module_settings[chat_id][setting_key] = enabled
            
            await self.save_permissions()
            
            status = "включен" if enabled else "отключен"
            logger.info(f"⚙️ Модуль {module_name} {status} для чата {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки модуля: {e}")
            return False
    
    async def get_chat_settings(self, chat_id: int) -> Dict[str, Any]:
        """📋 Получение настроек чата"""
        
        try:
            settings = {
                'chat_id': chat_id,
                'is_allowed': chat_id in self.allowed_chats if self.allowed_chats else True,
                'is_blocked': chat_id in self.blocked_chats,
                'has_whitelist': bool(self.allowed_chats),
                'modules': self.module_settings.get(chat_id, self.default_settings.copy()),
                'restricted_commands': []
            }
            
            # Ищем ограниченные команды
            for command, restricted_chats in self.command_restrictions.items():
                if restricted_chats and chat_id not in restricted_chats:
                    settings['restricted_commands'].append(command)
            
            return settings
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения настроек чата: {e}")
            return {}
    
    async def get_global_settings(self) -> Dict[str, Any]:
        """🌍 Получение глобальных настроек"""
        
        try:
            return {
                'allowed_chats': list(self.allowed_chats),
                'blocked_chats': list(self.blocked_chats),
                'allowed_users': list(self.allowed_users),
                'blocked_users': list(self.blocked_users),
                'total_chat_restrictions': len(self.allowed_chats) + len(self.blocked_chats),
                'total_user_restrictions': len(self.allowed_users) + len(self.blocked_users),
                'command_restrictions': {
                    cmd: list(chats) for cmd, chats in self.command_restrictions.items()
                },
                'configured_chats': len(self.module_settings),
                'default_settings': self.default_settings
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения глобальных настроек: {e}")
            return {}
    
    def get_module_info(self) -> Dict[str, Any]:
        """ℹ️ Информация о модуле"""
        
        return {
            'module_name': 'Permissions Module',
            'version': '3.0',
            'allowed_chats': len(self.allowed_chats),
            'blocked_chats': len(self.blocked_chats),
            'configured_chats': len(self.module_settings),
            'command_restrictions': len(self.command_restrictions),
            'status': 'active'
        }


__all__ = ["PermissionsModule"]