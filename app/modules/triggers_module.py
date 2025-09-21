#!/usr/bin/env python3
"""
⚡ TRIGGERS MODULE v3.0 - ИСПРАВЛЕНО
🎯 Продвинутая система триггеров

Система создания, управления и выполнения пользовательских триггеров
"""

import logging
import json
import re
import asyncio  # ДОБАВЛЕН ИМПОРТ
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class TriggersModule:
    """⚡ Модуль системы триггеров"""
    
    def __init__(self, db_service, config):
        self.db = db_service
        self.config = config
        
        # Файл с триггерами
        self.triggers_file = Path('data/triggers/triggers.json')
        self.triggers_file.parent.mkdir(exist_ok=True)
        
        # Кэш триггеров
        self.triggers = {}
        self.global_triggers = {}
        
        # Статистика срабатывания
        self.trigger_stats = {}
        
        # Типы триггеров
        self.trigger_types = {
            'text': 'Текстовый триггер',
            'regex': 'Регулярное выражение',
            'exact': 'Точное совпадение',
            'contains': 'Содержит текст',
            'starts_with': 'Начинается с',
            'ends_with': 'Заканчивается на'
        }
        
        # Загружаем существующие триггеры - БЕЗ asyncio.create_task при инициализации
        logger.info("⚡ Triggers Module инициализирован")
    
    async def initialize(self):
        """📥 Отложенная инициализация триггеров"""
        await self.load_triggers()
    
    async def load_triggers(self):
        """📥 Загрузка триггеров из файла"""
        
        try:
            if self.triggers_file.exists():
                with open(self.triggers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.triggers = data.get('chat_triggers', {})
                    self.global_triggers = data.get('global_triggers', {})
                    self.trigger_stats = data.get('statistics', {})
                
                logger.info(f"📥 Загружено триггеров: {len(self.triggers)} чатовых, {len(self.global_triggers)} глобальных")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки триггеров: {e}")
    
    async def save_triggers(self):
        """💾 Сохранение триггеров в файл"""
        
        try:
            data = {
                'chat_triggers': self.triggers,
                'global_triggers': self.global_triggers,
                'statistics': self.trigger_stats,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.triggers_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.debug("💾 Триггеры сохранены")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения триггеров: {e}")
            return False
    
    async def add_trigger(self, user_id: int, chat_id: int, trigger_name: str, 
                         trigger_pattern: str, response: str, 
                         trigger_type: str = 'contains') -> Dict[str, Any]:
        """➕ Добавление нового триггера"""
        
        try:
            # Валидация входных данных
            if not all([trigger_name, trigger_pattern, response]):
                return {
                    'success': False,
                    'error': 'Все поля должны быть заполнены'
                }
            
            if trigger_type not in self.trigger_types:
                return {
                    'success': False,
                    'error': f'Неизвестный тип триггера. Доступные: {", ".join(self.trigger_types.keys())}'
                }
            
            # Проверяем лимиты
            if not await self._check_trigger_limits(user_id, chat_id):
                return {
                    'success': False,
                    'error': 'Достигнут лимит количества триггеров'
                }
            
            # Создаем триггер
            trigger_data = {
                'id': f"{chat_id}_{trigger_name}_{int(datetime.now().timestamp())}",
                'name': trigger_name,
                'pattern': trigger_pattern,
                'response': response,
                'type': trigger_type,
                'creator_id': user_id,
                'chat_id': chat_id,
                'created_at': datetime.now().isoformat(),
                'usage_count': 0,
                'is_active': True,
                'is_global': chat_id == 0  # Глобальные триггеры имеют chat_id = 0
            }
            
            # Сохраняем триггер
            if trigger_data['is_global']:
                self.global_triggers[trigger_data['id']] = trigger_data
            else:
                chat_key = str(chat_id)
                if chat_key not in self.triggers:
                    self.triggers[chat_key] = {}
                self.triggers[chat_key][trigger_data['id']] = trigger_data
            
            # Сохраняем в файл
            await self.save_triggers()
            
            # Логируем создание
            if self.db:
                await self.db.track_event(
                    user_id, chat_id, 'trigger_created',
                    {'trigger_name': trigger_name, 'trigger_type': trigger_type}
                )
            
            return {
                'success': True,
                'trigger_id': trigger_data['id'],
                'message': f'Триггер "{trigger_name}" создан успешно'
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания триггера: {e}")
            return {
                'success': False,
                'error': f'Ошибка создания триггера: {str(e)}'
            }
    
    async def delete_trigger(self, user_id: int, chat_id: int, 
                           trigger_identifier: str) -> Dict[str, Any]:
        """🗑️ Удаление триггера"""
        
        try:
            # Ищем триггер
            trigger_data = await self._find_trigger(chat_id, trigger_identifier)
            
            if not trigger_data:
                return {
                    'success': False,
                    'error': 'Триггер не найден'
                }
            
            # Проверяем права на удаление
            if not await self._check_trigger_permissions(user_id, chat_id, trigger_data):
                return {
                    'success': False,
                    'error': 'Недостаточно прав для удаления этого триггера'
                }
            
            # Удаляем триггер
            if trigger_data['is_global']:
                del self.global_triggers[trigger_data['id']]
            else:
                chat_key = str(chat_id)
                if chat_key in self.triggers and trigger_data['id'] in self.triggers[chat_key]:
                    del self.triggers[chat_key][trigger_data['id']]
            
            # Сохраняем изменения
            await self.save_triggers()
            
            # Логируем удаление
            if self.db:
                await self.db.track_event(
                    user_id, chat_id, 'trigger_deleted',
                    {'trigger_name': trigger_data['name']}
                )
            
            return {
                'success': True,
                'message': f'Триггер "{trigger_data["name"]}" удален'
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления триггера: {e}")
            return {
                'success': False,
                'error': f'Ошибка удаления: {str(e)}'
            }
    
    async def check_message_triggers(self, message_text: str, chat_id: int, 
                                   user_id: int) -> Optional[str]:
        """🎯 Проверка сообщения на соответствие триггерам"""
        
        try:
            if not message_text:
                return None
            
            # Получаем триггеры для этого чата
            chat_triggers = self.triggers.get(str(chat_id), {})
            
            # Проверяем чатовые триггеры
            response = await self._check_triggers(message_text, chat_triggers, user_id, chat_id)
            if response:
                return response
            
            # Проверяем глобальные триггеры
            response = await self._check_triggers(message_text, self.global_triggers, user_id, chat_id)
            if response:
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки триггеров: {e}")
            return None
    
    async def _check_triggers(self, message_text: str, triggers: Dict, 
                            user_id: int, chat_id: int) -> Optional[str]:
        """🔍 Проверка сообщения против набора триггеров"""
        
        try:
            for trigger_id, trigger_data in triggers.items():
                if not trigger_data.get('is_active', True):
                    continue
                
                # Проверяем соответствие
                if await self._match_trigger(message_text, trigger_data):
                    # Увеличиваем счетчик использования
                    trigger_data['usage_count'] = trigger_data.get('usage_count', 0) + 1
                    trigger_data['last_used'] = datetime.now().isoformat()
                    
                    # Обновляем статистику
                    if trigger_id not in self.trigger_stats:
                        self.trigger_stats[trigger_id] = 0
                    self.trigger_stats[trigger_id] += 1
                    
                    # Сохраняем статистику
                    asyncio.create_task(self.save_triggers())
                    
                    # Логируем срабатывание
                    if self.db:
                        await self.db.track_event(
                            user_id, chat_id, 'trigger_activated',
                            {'trigger_name': trigger_data['name'], 'trigger_id': trigger_id}
                        )
                    
                    # Обрабатываем ответ триггера
                    return await self._process_trigger_response(
                        trigger_data['response'], user_id, chat_id, message_text
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке набора триггеров: {e}")
            return None
    
    async def _match_trigger(self, message_text: str, trigger_data: Dict) -> bool:
        """🎯 Проверка соответствия сообщения триггеру"""
        
        try:
            pattern = trigger_data['pattern']
            trigger_type = trigger_data.get('type', 'contains')
            
            # Приводим к нижнему регистру для сравнения
            message_lower = message_text.lower()
            pattern_lower = pattern.lower()
            
            if trigger_type == 'exact':
                return message_lower == pattern_lower
            elif trigger_type == 'contains':
                return pattern_lower in message_lower
            elif trigger_type == 'starts_with':
                return message_lower.startswith(pattern_lower)
            elif trigger_type == 'ends_with':
                return message_lower.endswith(pattern_lower)
            elif trigger_type == 'regex':
                try:
                    return bool(re.search(pattern, message_text, re.IGNORECASE))
                except re.error:
                    logger.warning(f"⚠️ Некорректное регулярное выражение в триггере: {pattern}")
                    return False
            else:
                # По умолчанию - contains
                return pattern_lower in message_lower
                
        except Exception as e:
            logger.error(f"❌ Ошибка сопоставления триггера: {e}")
            return False
    
    async def _process_trigger_response(self, response: str, user_id: int, 
                                      chat_id: int, original_message: str) -> str:
        """🔧 Обработка ответа триггера с заменой переменных"""
        
        try:
            processed_response = response
            
            # Заменяем переменные
            replacements = {
                '{user_id}': str(user_id),
                '{chat_id}': str(chat_id),
                '{message}': original_message,
                '{time}': datetime.now().strftime('%H:%M'),
                '{date}': datetime.now().strftime('%d.%m.%Y'),
                '{datetime}': datetime.now().strftime('%d.%m.%Y %H:%M')
            }
            
            for placeholder, value in replacements.items():
                processed_response = processed_response.replace(placeholder, value)
            
            return processed_response
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки ответа триггера: {e}")
            return response
    
    async def _find_trigger(self, chat_id: int, identifier: str) -> Optional[Dict]:
        """🔍 Поиск триггера по идентификатору или имени"""
        
        try:
            # Сначала ищем по ID
            chat_key = str(chat_id)
            
            # Поиск в чатовых триггерах
            if chat_key in self.triggers:
                if identifier in self.triggers[chat_key]:
                    return self.triggers[chat_key][identifier]
                
                # Поиск по имени
                for trigger_data in self.triggers[chat_key].values():
                    if trigger_data['name'].lower() == identifier.lower():
                        return trigger_data
            
            # Поиск в глобальных триггерах
            if identifier in self.global_triggers:
                return self.global_triggers[identifier]
            
            for trigger_data in self.global_triggers.values():
                if trigger_data['name'].lower() == identifier.lower():
                    return trigger_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска триггера: {e}")
            return None
    
    async def _check_trigger_permissions(self, user_id: int, chat_id: int, 
                                       trigger_data: Dict) -> bool:
        """🔒 Проверка прав доступа к триггеру"""
        
        try:
            # Админы могут все
            if user_id in self.config.bot.admin_ids:
                return True
            
            # Создатель может управлять своим триггером
            if trigger_data.get('creator_id') == user_id:
                return True
            
            # Для глобальных триггеров нужны права админа
            if trigger_data.get('is_global', False):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки прав доступа: {e}")
            return False
    
    async def _check_trigger_limits(self, user_id: int, chat_id: int) -> bool:
        """📊 Проверка лимитов на создание триггеров"""
        
        try:
            # Лимиты для разных пользователей
            if user_id in self.config.bot.admin_ids:
                max_triggers = 100  # Админы могут создавать много триггеров
            else:
                max_triggers = 10   # Обычные пользователи ограничены
            
            # Подсчитываем существующие триггеры пользователя
            user_triggers_count = 0
            
            chat_key = str(chat_id)
            if chat_key in self.triggers:
                for trigger_data in self.triggers[chat_key].values():
                    if trigger_data.get('creator_id') == user_id:
                        user_triggers_count += 1
            
            return user_triggers_count < max_triggers
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки лимитов: {e}")
            return True  # В случае ошибки разрешаем
    
    async def get_user_triggers(self, user_id: int, chat_id: int) -> List[Dict]:
        """📋 Получение списка триггеров пользователя"""
        
        try:
            user_triggers = []
            
            # Триггеры в текущем чате
            chat_key = str(chat_id)
            if chat_key in self.triggers:
                for trigger_data in self.triggers[chat_key].values():
                    if trigger_data.get('creator_id') == user_id:
                        user_triggers.append(trigger_data)
            
            # Глобальные триггеры пользователя
            for trigger_data in self.global_triggers.values():
                if trigger_data.get('creator_id') == user_id:
                    user_triggers.append(trigger_data)
            
            # Сортируем по дате создания
            user_triggers.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return user_triggers
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения триггеров пользователя: {e}")
            return []
    
    async def get_trigger_statistics(self) -> Dict[str, Any]:
        """📊 Получение статистики триггеров"""
        
        try:
            total_triggers = len(self.global_triggers)
            for chat_triggers in self.triggers.values():
                total_triggers += len(chat_triggers)
            
            active_triggers = 0
            total_usage = 0
            
            # Подсчитываем активные триггеры и общее использование
            for trigger_data in self.global_triggers.values():
                if trigger_data.get('is_active', True):
                    active_triggers += 1
                total_usage += trigger_data.get('usage_count', 0)
            
            for chat_triggers in self.triggers.values():
                for trigger_data in chat_triggers.values():
                    if trigger_data.get('is_active', True):
                        active_triggers += 1
                    total_usage += trigger_data.get('usage_count', 0)
            
            # Топ-5 самых используемых триггеров
            top_triggers = []
            all_triggers = list(self.global_triggers.values())
            for chat_triggers in self.triggers.values():
                all_triggers.extend(chat_triggers.values())
            
            all_triggers.sort(key=lambda x: x.get('usage_count', 0), reverse=True)
            top_triggers = all_triggers[:5]
            
            return {
                'total_triggers': total_triggers,
                'active_triggers': active_triggers,
                'global_triggers': len(self.global_triggers),
                'chat_triggers': total_triggers - len(self.global_triggers),
                'total_usage': total_usage,
                'top_triggers': [
                    {
                        'name': t['name'],
                        'usage_count': t.get('usage_count', 0),
                        'type': t.get('type', 'contains')
                    }
                    for t in top_triggers
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def get_module_info(self) -> Dict[str, Any]:
        """ℹ️ Информация о модуле"""
        
        return {
            'module_name': 'Triggers Module',
            'version': '3.0',
            'loaded_triggers': len(self.triggers),
            'global_triggers': len(self.global_triggers),
            'trigger_types': list(self.trigger_types.keys()),
            'status': 'active'
        }


__all__ = ["TriggersModule"]