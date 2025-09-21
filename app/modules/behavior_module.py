#!/usr/bin/env python3
"""
🌟 BEHAVIOR MODULE v2.0
🎭 Модуль адаптивного поведения и машинного обучения

Анализ поведения пользователей и адаптация ответов под их стиль
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class BehaviorModule:
    """🌟 Модуль адаптивного поведения"""
    
    def __init__(self, db_service, ai_service):
        self.db = db_service
        self.ai = ai_service
        
        # Профили поведения пользователей
        self.user_profiles = {}
        
        # Паттерны поведения
        self.behavior_patterns = {
            'communication_styles': {
                'formal': {'keywords': ['пожалуйста', 'спасибо', 'извините'], 'score': 0},
                'casual': {'keywords': ['привет', 'пока', 'круто'], 'score': 0},
                'technical': {'keywords': ['функция', 'алгоритм', 'код'], 'score': 0},
                'emotional': {'keywords': ['чувствую', 'переживаю', 'радуюсь'], 'score': 0}
            },
            'interaction_types': {
                'question_asker': {'pattern': 'high_question_ratio', 'threshold': 0.7},
                'helper_seeker': {'pattern': 'help_requests', 'threshold': 0.5},
                'information_consumer': {'pattern': 'long_responses_preference', 'threshold': 0.6},
                'experimenter': {'pattern': 'diverse_commands', 'threshold': 0.8}
            }
        }
        
        # Конфигурация обучения
        self.learning_config = {
            'min_interactions_for_profile': 5,
            'profile_update_frequency': 24,  # часы
            'adaptation_strength': 0.3
        }
        
        logger.info("🌟 Behavior Module инициализирован")
    
    async def analyze_user_behavior(self, user_id: int, chat_id: int, 
                                   message: str, context: Dict = None) -> Dict[str, Any]:
        """🔍 Анализ поведения пользователя"""
        
        try:
            # Получаем профиль пользователя
            profile = await self._get_user_profile(user_id)
            
            # Анализируем текущее сообщение
            message_analysis = self._analyze_message(message)
            
            # Обновляем профиль с новыми данными
            updated_profile = self._update_profile(profile, message_analysis)
            
            # Сохраняем обновленный профиль
            await self._save_user_profile(user_id, updated_profile)
            
            # Генерируем анализ поведения
            behavior_analysis = {
                'user_id': user_id,
                'user_type': updated_profile.get('user_type', 'regular_user'),
                'communication_style': updated_profile.get('communication_style', 'neutral'),
                'interaction_pattern': updated_profile.get('interaction_pattern', 'balanced'),
                'preferences': updated_profile.get('preferences', {}),
                'confidence_score': updated_profile.get('confidence_score', 0.5),
                'total_interactions': updated_profile.get('total_interactions', 0),
                'last_analysis': datetime.now().isoformat()
            }
            
            return behavior_analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа поведения пользователя: {e}")
            return {
                'user_type': 'unknown',
                'communication_style': 'neutral',
                'error': str(e)
            }
    
    async def adapt_response(self, user_id: int, base_response: str, 
                           behavior_analysis: Dict) -> str:
        """🎯 Адаптация ответа под пользователя"""
        
        try:
            user_type = behavior_analysis.get('user_type', 'regular_user')
            communication_style = behavior_analysis.get('communication_style', 'neutral')
            preferences = behavior_analysis.get('preferences', {})
            
            # Применяем адаптации
            adapted_response = base_response
            
            # Адаптация по типу пользователя
            if user_type == 'technical_user':
                adapted_response = self._add_technical_details(adapted_response)
            elif user_type == 'casual_user':
                adapted_response = self._make_more_casual(adapted_response)
            elif user_type == 'helper_seeker':
                adapted_response = self._add_helpful_suggestions(adapted_response)
            
            # Адаптация по стилю общения
            if communication_style == 'formal':
                adapted_response = self._make_more_formal(adapted_response)
            elif communication_style == 'emotional':
                adapted_response = self._add_emotional_support(adapted_response)
            elif communication_style == 'concise':
                adapted_response = self._make_more_concise(adapted_response)
            
            # Адаптация по предпочтениям
            if preferences.get('likes_details', False):
                adapted_response = self._add_more_details(adapted_response)
            
            if preferences.get('uses_emojis', False):
                adapted_response = self._add_appropriate_emojis(adapted_response)
            
            return adapted_response
            
        except Exception as e:
            logger.error(f"❌ Ошибка адаптации ответа: {e}")
            return base_response
    
    async def learn_from_interaction(self, user_id: int, chat_id: int, 
                                   user_message: str, bot_response: str) -> bool:
        """📚 Обучение на основе взаимодействия"""
        
        try:
            # Получаем текущий профиль
            profile = await self._get_user_profile(user_id)
            
            # Анализируем взаимодействие
            interaction_data = {
                'user_message': user_message,
                'bot_response': bot_response,
                'timestamp': datetime.now().isoformat(),
                'message_analysis': self._analyze_message(user_message),
                'response_effectiveness': self._estimate_response_effectiveness(user_message, bot_response)
            }
            
            # Обновляем обучающие данные
            if 'learning_data' not in profile:
                profile['learning_data'] = []
            
            profile['learning_data'].append(interaction_data)
            
            # Ограничиваем размер обучающих данных
            if len(profile['learning_data']) > 100:
                profile['learning_data'] = profile['learning_data'][-100:]
            
            # Переобучаем модель поведения
            await self._retrain_behavior_model(user_id, profile)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения на взаимодействии: {e}")
            return False
    
    async def _get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """👤 Получение профиля пользователя"""
        
        try:
            # Проверяем кэш
            if user_id in self.user_profiles:
                profile = self.user_profiles[user_id]
                # Проверяем свежесть профиля
                last_update = datetime.fromisoformat(profile.get('last_update', datetime.now().isoformat()))
                if datetime.now() - last_update < timedelta(hours=self.learning_config['profile_update_frequency']):
                    return profile
            
            # В реальной реализации здесь был бы запрос к БД
            # Для демонстрации создаем базовый профиль
            profile = {
                'user_id': user_id,
                'user_type': 'regular_user',
                'communication_style': 'neutral',
                'interaction_pattern': 'balanced',
                'preferences': {},
                'confidence_score': 0.5,
                'total_interactions': 0,
                'last_update': datetime.now().isoformat(),
                'learning_data': []
            }
            
            # Сохраняем в кэш
            self.user_profiles[user_id] = profile
            
            return profile
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения профиля пользователя: {e}")
            return {
                'user_id': user_id,
                'user_type': 'unknown',
                'communication_style': 'neutral'
            }
    
    async def _save_user_profile(self, user_id: int, profile: Dict[str, Any]) -> bool:
        """💾 Сохранение профиля пользователя"""
        
        try:
            profile['last_update'] = datetime.now().isoformat()
            
            # Сохраняем в кэш
            self.user_profiles[user_id] = profile
            
            # В реальной реализации здесь был бы запрос к БД
            logger.debug(f"💾 Профиль пользователя {user_id} сохранен")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения профиля: {e}")
            return False
    
    def _analyze_message(self, message: str) -> Dict[str, Any]:
        """📊 Анализ сообщения пользователя"""
        
        try:
            analysis = {
                'length': len(message),
                'word_count': len(message.split()),
                'has_questions': '?' in message,
                'has_exclamations': '!' in message,
                'has_emojis': any(ord(char) > 127 for char in message),
                'sentiment': self._analyze_sentiment(message),
                'communication_style': self._detect_communication_style(message),
                'topic_keywords': self._extract_keywords(message),
                'complexity_level': self._assess_complexity(message)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа сообщения: {e}")
            return {}
    
    def _analyze_sentiment(self, message: str) -> str:
        """😊 Анализ настроения сообщения"""
        
        try:
            message_lower = message.lower()
            
            positive_words = ['хорошо', 'отлично', 'супер', 'класс', 'спасибо', 'радуюсь']
            negative_words = ['плохо', 'ужасно', 'проблема', 'ошибка', 'не работает']
            neutral_words = ['вопрос', 'помощь', 'информация']
            
            positive_score = sum(1 for word in positive_words if word in message_lower)
            negative_score = sum(1 for word in negative_words if word in message_lower)
            
            if positive_score > negative_score:
                return 'positive'
            elif negative_score > positive_score:
                return 'negative'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа настроения: {e}")
            return 'neutral'
    
    def _detect_communication_style(self, message: str) -> str:
        """🗣️ Определение стиля общения"""
        
        try:
            message_lower = message.lower()
            
            formal_markers = ['пожалуйста', 'благодарю', 'извините', 'могли бы']
            casual_markers = ['привет', 'пока', 'круто', 'ок']
            technical_markers = ['функция', 'алгоритм', 'код', 'программа']
            emotional_markers = ['чувствую', 'переживаю', 'волнуюсь', 'радуюсь']
            
            scores = {
                'formal': sum(1 for marker in formal_markers if marker in message_lower),
                'casual': sum(1 for marker in casual_markers if marker in message_lower),
                'technical': sum(1 for marker in technical_markers if marker in message_lower),
                'emotional': sum(1 for marker in emotional_markers if marker in message_lower)
            }
            
            # Возвращаем стиль с максимальным счетом
            max_style = max(scores, key=scores.get)
            
            if scores[max_style] > 0:
                return max_style
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"❌ Ошибка определения стиля общения: {e}")
            return 'neutral'
    
    def _extract_keywords(self, message: str) -> List[str]:
        """🔑 Извлечение ключевых слов"""
        
        try:
            stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'что', 'это'}
            
            words = message.lower().split()
            keywords = []
            
            for word in words:
                clean_word = ''.join(c for c in word if c.isalnum())
                if len(clean_word) > 2 and clean_word not in stop_words and clean_word.isalpha():
                    keywords.append(clean_word)
            
            return list(set(keywords))[:10]
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения ключевых слов: {e}")
            return []
    
    def _assess_complexity(self, message: str) -> str:
        """🧠 Оценка сложности сообщения"""
        
        try:
            word_count = len(message.split())
            avg_word_length = sum(len(word) for word in message.split()) / max(word_count, 1)
            
            if word_count > 50 or avg_word_length > 6:
                return 'complex'
            elif word_count > 20 or avg_word_length > 4:
                return 'medium'
            else:
                return 'simple'
                
        except Exception as e:
            logger.error(f"❌ Ошибка оценки сложности: {e}")
            return 'medium'
    
    def _update_profile(self, profile: Dict[str, Any], message_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """🔄 Обновление профиля пользователя"""
        
        try:
            updated_profile = profile.copy()
            updated_profile['total_interactions'] += 1
            
            # Обновляем стиль общения
            current_style = message_analysis.get('communication_style', 'neutral')
            if current_style != 'neutral':
                updated_profile['communication_style'] = current_style
            
            # Обновляем предпочтения
            preferences = updated_profile.get('preferences', {})
            
            if message_analysis.get('has_emojis', False):
                preferences['uses_emojis'] = True
            
            if message_analysis.get('length', 0) > 100:
                preferences['likes_details'] = True
            
            updated_profile['preferences'] = preferences
            
            # Определяем тип пользователя
            total_interactions = updated_profile['total_interactions']
            if total_interactions >= self.learning_config['min_interactions_for_profile']:
                updated_profile['user_type'] = self._classify_user_type(updated_profile)
                updated_profile['confidence_score'] = min(0.9, total_interactions / 20)
            
            return updated_profile
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления профиля: {e}")
            return profile
    
    def _classify_user_type(self, profile: Dict[str, Any]) -> str:
        """🎭 Классификация типа пользователя"""
        
        try:
            preferences = profile.get('preferences', {})
            communication_style = profile.get('communication_style', 'neutral')
            
            # Правила классификации
            if communication_style == 'technical':
                return 'technical_user'
            elif communication_style == 'casual':
                return 'casual_user'
            elif preferences.get('likes_details', False):
                return 'information_seeker'
            elif communication_style == 'emotional':
                return 'support_seeker'
            else:
                return 'regular_user'
                
        except Exception as e:
            logger.error(f"❌ Ошибка классификации типа пользователя: {e}")
            return 'regular_user'
    
    def _estimate_response_effectiveness(self, user_message: str, bot_response: str) -> float:
        """📊 Оценка эффективности ответа"""
        
        try:
            # Простая эвристическая оценка
            effectiveness = 0.5  # Базовый уровень
            
            # Проверяем соответствие длины ответа запросу
            message_length = len(user_message)
            response_length = len(bot_response)
            
            if message_length > 100 and response_length > 200:
                effectiveness += 0.2  # Подробный ответ на подробный вопрос
            elif message_length < 50 and response_length < 150:
                effectiveness += 0.1  # Краткий ответ на краткий вопрос
            
            # Проверяем наличие вопроса и ответа
            if '?' in user_message and len(bot_response) > 50:
                effectiveness += 0.2  # Развернутый ответ на вопрос
            
            return min(1.0, effectiveness)
            
        except Exception as e:
            logger.error(f"❌ Ошибка оценки эффективности ответа: {e}")
            return 0.5
    
    async def _retrain_behavior_model(self, user_id: int, profile: Dict[str, Any]) -> bool:
        """🤖 Переобучение модели поведения"""
        
        try:
            learning_data = profile.get('learning_data', [])
            
            if len(learning_data) < 10:
                return False  # Недостаточно данных для переобучения
            
            # Анализируем паттерны в обучающих данных
            patterns = self._analyze_interaction_patterns(learning_data)
            
            # Обновляем профиль на основе найденных паттернов
            profile['interaction_patterns'] = patterns
            profile['model_last_trained'] = datetime.now().isoformat()
            
            logger.debug(f"🤖 Модель поведения пользователя {user_id} переобучена")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка переобучения модели: {e}")
            return False
    
    def _analyze_interaction_patterns(self, learning_data: List[Dict]) -> Dict[str, Any]:
        """🔍 Анализ паттернов взаимодействий"""
        
        try:
            patterns = {
                'preferred_response_length': 'medium',
                'communication_times': [],
                'topic_preferences': [],
                'interaction_frequency': 'regular'
            }
            
            # Анализируем длины ответов
            response_lengths = []
            for interaction in learning_data:
                response_effectiveness = interaction.get('response_effectiveness', 0.5)
                bot_response = interaction.get('bot_response', '')
                
                if response_effectiveness > 0.7:  # Эффективные ответы
                    response_lengths.append(len(bot_response))
            
            if response_lengths:
                avg_effective_length = sum(response_lengths) / len(response_lengths)
                if avg_effective_length > 300:
                    patterns['preferred_response_length'] = 'long'
                elif avg_effective_length < 100:
                    patterns['preferred_response_length'] = 'short'
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа паттернов взаимодействий: {e}")
            return {}
    
    # Методы адаптации ответов
    
    def _add_technical_details(self, response: str) -> str:
        """🔧 Добавление технических деталей"""
        
        if len(response) < 200:
            return response + "\n\n💡 Если нужны дополнительные технические подробности, спрашивайте!"
        return response
    
    def _make_more_casual(self, response: str) -> str:
        """😊 Делаем ответ более неформальным"""
        
        casual_endings = [" 👍", " 😊", " Удачи!", " Надеюсь, помог!"]
        if not any(ending in response for ending in casual_endings):
            return response + " 😊"
        return response
    
    def _add_helpful_suggestions(self, response: str) -> str:
        """💡 Добавление полезных предложений"""
        
        if "?" not in response and len(response) < 300:
            return response + "\n\n💡 Если есть еще вопросы - смело спрашивайте!"
        return response
    
    def _make_more_formal(self, response: str) -> str:
        """🎩 Делаем ответ более официальным"""
        
        # Убираем эмодзи и неформальные выражения
        import re
        response = re.sub(r'[😀-🙏]', '', response)  # Убираем эмодзи
        
        if not response.endswith('.'):
            response += '.'
        
        return response
    
    def _add_emotional_support(self, response: str) -> str:
        """❤️ Добавление эмоциональной поддержки"""
        
        supportive_phrases = [
            "Понимаю ваши чувства.",
            "Это действительно важно.",
            "Вы на правильном пути."
        ]
        
        if len(response) < 200:
            return response + f"\n\n{supportive_phrases[0]}"
        return response
    
    def _make_more_concise(self, response: str) -> str:
        """✂️ Делаем ответ более кратким"""
        
        if len(response) > 300:
            # Берем первые два предложения
            sentences = response.split('.')
            return '. '.join(sentences[:2]) + '.'
        return response
    
    def _add_more_details(self, response: str) -> str:
        """📝 Добавление дополнительных деталей"""
        
        if len(response) < 200:
            return response + "\n\n📚 Хотите узнать больше подробностей по этой теме?"
        return response
    
    def _add_appropriate_emojis(self, response: str) -> str:
        """😊 Добавление подходящих эмодзи"""
        
        # Простая логика добавления эмодзи
        if 'спасибо' in response.lower() or 'благодарю' in response.lower():
            return response + " 🙏"
        elif 'помощь' in response.lower() or 'поможу' in response.lower():
            return response + " 💪"
        elif 'успех' in response.lower() or 'отлично' in response.lower():
            return response + " ✨"
        
        return response
    
    def get_module_stats(self) -> Dict[str, Any]:
        """📊 Статистика модуля"""
        
        return {
            'cached_profiles': len(self.user_profiles),
            'learning_enabled': bool(self.ai),
            'behavior_patterns_count': len(self.behavior_patterns),
            'module_status': 'active'
        }


__all__ = ["BehaviorModule"]