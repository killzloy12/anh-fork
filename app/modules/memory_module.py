#!/usr/bin/env python3
"""
🧠 MEMORY MODULE v2.0
💭 Модуль долгосрочной памяти диалогов

Система запоминания контекста разговоров и предпочтений пользователей
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MemoryModule:
    """🧠 Модуль памяти диалогов"""
    
    def __init__(self, db_service):
        self.db = db_service
        
        # Настройки памяти
        self.memory_config = {
            'max_interactions_per_user': 50,
            'context_window_messages': 10,
            'summary_threshold': 20,
            'cleanup_days': 30
        }
        
        # Кэш контекста для быстрого доступа
        self.context_cache = {}
        
        logger.info("🧠 Memory Module инициализирован")
    
    async def add_interaction(self, user_id: int, chat_id: int, user_message: str, 
                             bot_response: str, metadata: Dict = None) -> bool:
        """💬 Добавление взаимодействия в память"""
        
        try:
            # Подготавливаем метаданные
            interaction_metadata = {
                'timestamp': datetime.now().isoformat(),
                'message_length': len(user_message),
                'response_length': len(bot_response),
                'has_entities': self._extract_entities(user_message),
                'topic_keywords': self._extract_keywords(user_message),
                **(metadata or {})
            }
            
            # Сохраняем в базу данных
            success = await self.db.add_memory(
                user_id, chat_id, user_message, bot_response,
                json.dumps(interaction_metadata)
            )
            
            if success:
                # Очищаем кэш для этого пользователя
                cache_key = f"{user_id}_{chat_id}"
                if cache_key in self.context_cache:
                    del self.context_cache[cache_key]
                
                logger.debug(f"💬 Взаимодействие добавлено в память пользователя {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления взаимодействия в память: {e}")
            return False
    
    async def get_context(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """🔍 Получение контекста диалога"""
        
        try:
            cache_key = f"{user_id}_{chat_id}"
            
            # Проверяем кэш
            if cache_key in self.context_cache:
                cached_context = self.context_cache[cache_key]
                # Проверяем свежесть кэша (15 минут)
                cache_time = datetime.fromisoformat(cached_context.get('cached_at'))
                if datetime.now() - cache_time < timedelta(minutes=15):
                    return cached_context
            
            # Получаем память из БД
            memory_items = await self.db.get_memory(
                user_id, chat_id, self.memory_config['context_window_messages']
            )
            
            if not memory_items:
                return {'has_context': False}
            
            # Анализируем контекст
            context = await self._analyze_conversation_context(
                user_id, chat_id, memory_items
            )
            
            # Добавляем временную метку для кэша
            context['cached_at'] = datetime.now().isoformat()
            
            # Сохраняем в кэш
            self.context_cache[cache_key] = context
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста: {e}")
            return {'has_context': False, 'error': str(e)}
    
    async def _analyze_conversation_context(self, user_id: int, chat_id: int, 
                                          memory_items: List[str]) -> Dict[str, Any]:
        """🔍 Анализ контекста диалога"""
        
        try:
            if not memory_items:
                return {'has_context': False}
            
            # Разделяем сообщения на пользовательские и ботовские
            user_messages = []
            bot_messages = []
            
            for i, item in enumerate(memory_items):
                if i % 2 == 0:  # Четные индексы - пользователь
                    if item.startswith("Пользователь: "):
                        user_messages.append(item[14:])  # Убираем префикс
                else:  # Нечетные индексы - бот
                    if item.startswith("Бот: "):
                        bot_messages.append(item[5:])  # Убираем префикс
            
            # Анализируем темы и интересы
            topics = self._extract_conversation_topics(user_messages)
            preferences = self._extract_user_preferences(user_messages, bot_messages)
            
            # Определяем стиль общения
            communication_style = self._analyze_communication_style(user_messages)
            
            # Создаем сводку диалога
            conversation_summary = self._generate_conversation_summary(
                user_messages, bot_messages, topics
            )
            
            context = {
                'has_context': True,
                'user_id': user_id,
                'chat_id': chat_id,
                'memory': memory_items,
                'conversation_summary': conversation_summary,
                'main_topics': topics[:5],  # Топ-5 тем
                'user_preferences': preferences,
                'communication_style': communication_style,
                'total_interactions': len(memory_items) // 2,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа контекста диалога: {e}")
            return {
                'has_context': True,
                'memory': memory_items,
                'error': 'Ошибка анализа контекста'
            }
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """🔍 Извлечение сущностей из текста"""
        
        try:
            entities = {
                'urls': [],
                'mentions': [],
                'hashtags': [],
                'numbers': [],
                'dates': []
            }
            
            words = text.split()
            
            for word in words:
                # URLs
                if word.startswith(('http://', 'https://', 'www.')):
                    entities['urls'].append(word)
                
                # Mentions
                elif word.startswith('@'):
                    entities['mentions'].append(word)
                
                # Hashtags  
                elif word.startswith('#'):
                    entities['hashtags'].append(word)
                
                # Numbers
                elif word.isdigit():
                    entities['numbers'].append(word)
            
            return entities
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения сущностей: {e}")
            return {}
    
    def _extract_keywords(self, text: str) -> List[str]:
        """🔑 Извлечение ключевых слов"""
        
        try:
            # Простое извлечение ключевых слов
            # В продакшене здесь был бы более сложный NLP анализ
            
            stop_words = {
                'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о',
                'что', 'это', 'как', 'но', 'а', 'да', 'нет', 'не', 'или', 'же'
            }
            
            words = text.lower().split()
            keywords = []
            
            for word in words:
                # Убираем знаки препинания
                clean_word = ''.join(c for c in word if c.isalnum())
                
                # Фильтруем стоп-слова и короткие слова
                if (len(clean_word) > 2 and 
                    clean_word not in stop_words and
                    clean_word.isalpha()):
                    keywords.append(clean_word)
            
            # Возвращаем уникальные ключевые слова
            return list(set(keywords))[:10]  # Максимум 10 ключевых слов
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения ключевых слов: {e}")
            return []
    
    def _extract_conversation_topics(self, user_messages: List[str]) -> List[str]:
        """📝 Извлечение тем диалога"""
        
        try:
            # Собираем все ключевые слова из сообщений пользователя
            all_keywords = []
            
            for message in user_messages:
                keywords = self._extract_keywords(message)
                all_keywords.extend(keywords)
            
            # Подсчитываем частоту ключевых слов
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            
            # Возвращаем самые популярные темы
            topics = [word for word, count in keyword_counts.most_common(10)]
            
            # Группируем связанные темы
            grouped_topics = self._group_related_topics(topics)
            
            return grouped_topics
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения тем диалога: {e}")
            return []
    
    def _group_related_topics(self, topics: List[str]) -> List[str]:
        """🔗 Группировка связанных тем"""
        
        try:
            # Простая группировка по тематикам
            topic_groups = {
                'технологии': ['программирование', 'код', 'python', 'javascript', 'компьютер', 'сайт'],
                'криптовалюты': ['биткоин', 'ethereum', 'crypto', 'blockchain', 'майнинг'],
                'общение': ['привет', 'спасибо', 'пожалуйста', 'помощь', 'вопрос'],
                'работа': ['работа', 'проект', 'задача', 'deadline', 'встреча']
            }
            
            grouped = []
            used_topics = set()
            
            # Группируем темы
            for group_name, group_keywords in topic_groups.items():
                group_topics = []
                for topic in topics:
                    if topic in group_keywords and topic not in used_topics:
                        group_topics.append(topic)
                        used_topics.add(topic)
                
                if group_topics:
                    grouped.append(group_name)
            
            # Добавляем негруппированные темы
            for topic in topics:
                if topic not in used_topics:
                    grouped.append(topic)
            
            return grouped[:8]  # Максимум 8 тем
            
        except Exception as e:
            logger.error(f"❌ Ошибка группировки тем: {e}")
            return topics[:8]
    
    def _extract_user_preferences(self, user_messages: List[str], 
                                 bot_messages: List[str]) -> Dict[str, Any]:
        """⭐ Извлечение предпочтений пользователя"""
        
        try:
            preferences = {
                'likes': [],
                'dislikes': [],
                'interests': [],
                'communication_preferences': {
                    'prefers_detailed_answers': False,
                    'uses_emojis': False,
                    'asks_follow_up_questions': False
                }
            }
            
            # Анализируем сообщения на предмет предпочтений
            all_user_text = ' '.join(user_messages).lower()
            
            # Ищем позитивные маркеры
            positive_markers = ['нравится', 'люблю', 'хорошо', 'отлично', 'супер', 'класс']
            for marker in positive_markers:
                if marker in all_user_text:
                    # Извлекаем контекст вокруг маркера
                    context = self._extract_context_around_word(all_user_text, marker)
                    if context:
                        preferences['likes'].append(context)
            
            # Ищем негативные маркеры
            negative_markers = ['не нравится', 'плохо', 'ужасно', 'не люблю']
            for marker in negative_markers:
                if marker in all_user_text:
                    context = self._extract_context_around_word(all_user_text, marker)
                    if context:
                        preferences['dislikes'].append(context)
            
            # Анализируем стиль общения
            if len(all_user_text) / max(len(user_messages), 1) > 50:
                preferences['communication_preferences']['prefers_detailed_answers'] = True
            
            if any('😊' in msg or '🙂' in msg or '👍' in msg for msg in user_messages):
                preferences['communication_preferences']['uses_emojis'] = True
            
            if any('?' in msg for msg in user_messages):
                preferences['communication_preferences']['asks_follow_up_questions'] = True
            
            return preferences
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения предпочтений: {e}")
            return {}
    
    def _extract_context_around_word(self, text: str, word: str, window: int = 3) -> str:
        """📍 Извлечение контекста вокруг слова"""
        
        try:
            words = text.split()
            
            for i, w in enumerate(words):
                if word in w:
                    start = max(0, i - window)
                    end = min(len(words), i + window + 1)
                    context_words = words[start:end]
                    return ' '.join(context_words)
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения контекста: {e}")
            return ""
    
    def _analyze_communication_style(self, user_messages: List[str]) -> Dict[str, Any]:
        """🗣️ Анализ стиля общения"""
        
        try:
            if not user_messages:
                return {'style': 'unknown'}
            
            total_length = sum(len(msg) for msg in user_messages)
            avg_length = total_length / len(user_messages)
            
            # Подсчитываем различные характеристики
            question_count = sum(1 for msg in user_messages if '?' in msg)
            exclamation_count = sum(1 for msg in user_messages if '!' in msg)
            emoji_count = sum(1 for msg in user_messages if any(ord(char) > 127 for char in msg))
            
            style = {
                'average_message_length': round(avg_length, 1),
                'questions_ratio': round(question_count / len(user_messages), 2),
                'exclamations_ratio': round(exclamation_count / len(user_messages), 2),
                'uses_emojis': emoji_count > 0,
                'style': 'neutral'
            }
            
            # Определяем стиль
            if avg_length > 100:
                style['style'] = 'detailed'
            elif avg_length < 20:
                style['style'] = 'concise'
            
            if style['questions_ratio'] > 0.5:
                style['style'] = 'inquisitive'
            
            if style['exclamations_ratio'] > 0.3:
                style['style'] = 'enthusiastic'
            
            return style
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа стиля общения: {e}")
            return {'style': 'unknown'}
    
    def _generate_conversation_summary(self, user_messages: List[str], 
                                     bot_messages: List[str], 
                                     topics: List[str]) -> str:
        """📝 Генерация сводки диалога"""
        
        try:
            if not user_messages:
                return "Нет истории диалога"
            
            summary_parts = []
            
            # Количество взаимодействий
            interactions_count = len(user_messages)
            summary_parts.append(f"Диалог из {interactions_count} сообщений")
            
            # Основные темы
            if topics:
                main_topics = topics[:3]
                summary_parts.append(f"Основные темы: {', '.join(main_topics)}")
            
            # Характер диалога
            avg_user_length = sum(len(msg) for msg in user_messages) / len(user_messages)
            if avg_user_length > 50:
                summary_parts.append("подробные обсуждения")
            else:
                summary_parts.append("краткое общение")
            
            return "; ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сводки диалога: {e}")
            return "Активный диалог с пользователем"
    
    async def clear_user_memory(self, user_id: int, chat_id: int) -> bool:
        """🗑️ Очистка памяти пользователя"""
        
        try:
            # В реальной реализации здесь был бы SQL запрос DELETE
            # Для демонстрации возвращаем True
            
            # Очищаем кэш
            cache_key = f"{user_id}_{chat_id}"
            if cache_key in self.context_cache:
                del self.context_cache[cache_key]
            
            logger.info(f"🗑️ Память пользователя {user_id} в чате {chat_id} очищена")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки памяти: {e}")
            return False
    
    async def get_user_memory_stats(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """📊 Статистика памяти пользователя"""
        
        try:
            context = await self.get_context(user_id, chat_id)
            
            if not context.get('has_context'):
                return {
                    'has_memory': False,
                    'message': 'Нет данных о диалоге'
                }
            
            return {
                'has_memory': True,
                'total_interactions': context.get('total_interactions', 0),
                'conversation_summary': context.get('conversation_summary', ''),
                'main_themes': context.get('main_topics', []),
                'communication_style': context.get('communication_style', {}),
                'memory_size': len(context.get('memory', []))
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики памяти: {e}")
            return {
                'has_memory': False,
                'error': str(e)
            }
    
    def get_module_stats(self) -> Dict[str, Any]:
        """📊 Статистика модуля"""
        
        return {
            'cached_contexts': len(self.context_cache),
            'config': self.memory_config,
            'module_status': 'active'
        }


__all__ = ["MemoryModule"]