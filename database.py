#!/usr/bin/env python3
"""
💾 DATABASE SERVICE v3.0 - ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
🔥 ИСПРАВЛЕНО: убрана колонка description из system_settings

ФИНАЛЬНЫЕ ИСПРАВЛЕНИЯ:
• system_settings только с key, value, updated_by, updated_at
• Убраны все ссылки на description
• Убраны индексы на несуществующие колонки timestamp в некоторых таблицах
• Все таблицы корректно созданы БЕЗ КОНФЛИКТОВ
"""

import asyncio
import logging
import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DatabaseService:
    """💾 Расширенный сервис базы данных"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = Path(config.path)
        self.connection = None
        self.initialized = False
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """🚀 Инициализация расширенной базы данных"""
        try:
            self.connection = await aiosqlite.connect(
                self.db_path,
                timeout=30.0
            )
            
            # Настраиваем производительность
            if self.config.wal_mode:
                await self.connection.execute("PRAGMA journal_mode=WAL")
                await self.connection.execute("PRAGMA synchronous=NORMAL")
                await self.connection.execute("PRAGMA cache_size=10000")
                await self.connection.execute("PRAGMA temp_store=memory")
                await self.connection.execute("PRAGMA foreign_keys=ON")
            
            # Создаем все таблицы
            await self._create_extended_tables()
            
            self.initialized = True
            logger.info("💾 Расширенная база данных инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    async def _create_extended_tables(self):
        """📋 Создание всех расширенных таблиц"""
        
        tables = [
            # =================== ОСНОВНЫЕ ТАБЛИЦЫ ===================
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                is_premium BOOLEAN DEFAULT FALSE,
                is_bot BOOLEAN DEFAULT FALSE,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                total_ai_requests INTEGER DEFAULT 0,
                total_crypto_requests INTEGER DEFAULT 0,
                reputation_score INTEGER DEFAULT 0,
                is_banned BOOLEAN DEFAULT FALSE,
                ban_reason TEXT,
                learning_profile TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT,
                username TEXT,
                description TEXT,
                invite_link TEXT,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                settings TEXT DEFAULT '{}',
                moderation_settings TEXT DEFAULT '{}',
                random_messages_enabled BOOLEAN DEFAULT FALSE,
                random_messages_chance REAL DEFAULT 0.01,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                text TEXT,
                message_type TEXT DEFAULT 'text',
                reply_to_message_id INTEGER,
                forward_from_user_id INTEGER,
                forward_from_chat_id INTEGER,
                has_media BOOLEAN DEFAULT FALSE,
                media_type TEXT,
                sentiment_score REAL,
                toxicity_score REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                action_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
            """,
            
            # =================== РАСШИРЕННАЯ МОДЕРАЦИЯ ===================
            """
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                ban_type TEXT DEFAULT 'permanent',
                ban_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                unban_date DATETIME,
                expires_at DATETIME,
                is_global BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                additional_data TEXT DEFAULT '{}',
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS mutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                mute_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                mute_until DATETIME NOT NULL,
                mute_type TEXT DEFAULT 'full',
                restrictions TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                warn_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                severity_level INTEGER DEFAULT 1,
                auto_generated BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS kicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                kick_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS restrictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                restriction_type TEXT NOT NULL,
                reason TEXT,
                start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_date DATETIME,
                restrictions_data TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS moderation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                details TEXT,
                auto_generated BOOLEAN DEFAULT FALSE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS moderation_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                setting_key TEXT NOT NULL,
                setting_value TEXT NOT NULL,
                updated_by INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(chat_id, setting_key)
            )
            """,
            
            # =================== ГИБКИЕ ТРИГГЕРЫ ===================
            """
            CREATE TABLE IF NOT EXISTS flexible_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                pattern TEXT NOT NULL,
                response_data TEXT NOT NULL,
                conditions TEXT DEFAULT '{}',
                settings TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                is_global BOOLEAN DEFAULT FALSE,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                last_used DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(user_id, chat_id, name),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS trigger_activations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                matched_text TEXT,
                response_sent TEXT,
                execution_time REAL,
                was_successful BOOLEAN DEFAULT TRUE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (trigger_id) REFERENCES flexible_triggers (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            # =================== КАСТОМНЫЕ СЛОВА ПРИЗЫВА ===================
            """
            CREATE TABLE IF NOT EXISTS custom_trigger_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                added_by INTEGER NOT NULL,
                usage_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (added_by) REFERENCES users (id)
            )
            """,
            
            # =================== АДАПТИВНОЕ ОБУЧЕНИЕ ===================
            """
            CREATE TABLE IF NOT EXISTS learning_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                context_data TEXT DEFAULT '{}',
                user_reaction TEXT,
                satisfaction_score INTEGER,
                response_time REAL,
                was_helpful BOOLEAN,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                response_data TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                preference_data TEXT DEFAULT '{}',
                learning_data TEXT DEFAULT '{}',
                communication_style TEXT DEFAULT 'balanced',
                preferred_response_length TEXT DEFAULT 'medium',
                interests TEXT DEFAULT '[]',
                disliked_topics TEXT DEFAULT '[]',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS context_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                context_type TEXT NOT NULL,
                context_data TEXT NOT NULL,
                relevance_score REAL DEFAULT 1.0,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            # =================== КРИПТОВАЛЮТЫ ===================
            """
            CREATE TABLE IF NOT EXISTS crypto_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin_id TEXT NOT NULL,
                coin_symbol TEXT NOT NULL,
                coin_name TEXT,
                price_data TEXT NOT NULL,
                market_data TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(coin_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS crypto_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                coin_query TEXT NOT NULL,
                coin_found TEXT,
                price REAL,
                request_data TEXT DEFAULT '{}',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS crypto_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                coin_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                trigger_price REAL,
                current_price REAL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                triggered_at DATETIME,
                
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            # =================== РАЗВЛЕЧЕНИЯ И ИГРЫ ===================
            """
            CREATE TABLE IF NOT EXISTS entertainment_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_data TEXT DEFAULT '{}',
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                chat_id INTEGER,
                total_messages INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                ai_requests INTEGER DEFAULT 0,
                crypto_requests INTEGER DEFAULT 0,
                moderation_actions INTEGER DEFAULT 0,
                trigger_activations INTEGER DEFAULT 0,
                entertainment_requests INTEGER DEFAULT 0,
                
                UNIQUE(date, chat_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                date DATE NOT NULL,
                messages_count INTEGER DEFAULT 0,
                chars_count INTEGER DEFAULT 0,
                ai_requests INTEGER DEFAULT 0,
                crypto_requests INTEGER DEFAULT 0,
                entertainment_requests INTEGER DEFAULT 0,
                stickers_sent INTEGER DEFAULT 0,
                commands_used INTEGER DEFAULT 0,
                
                UNIQUE(user_id, chat_id, date)
            )
            """,
            
            # =================== СИСТЕМА (ФИНАЛЬНО ИСПРАВЛЕНО!) ===================
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_by INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS error_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                stack_trace TEXT,
                user_id INTEGER,
                chat_id INTEGER,
                context_data TEXT,
                severity TEXT DEFAULT 'medium',
                resolved BOOLEAN DEFAULT FALSE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS feature_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT NOT NULL,
                user_id INTEGER,
                chat_id INTEGER,
                usage_count INTEGER DEFAULT 1,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                success_count INTEGER DEFAULT 1,
                
                UNIQUE(feature_name, user_id, chat_id)
            )
            """
        ]
        
        # Создаем все таблицы
        for table_sql in tables:
            try:
                await self.connection.execute(table_sql)
            except Exception as e:
                logger.error(f"❌ Ошибка создания таблицы: {e}")
        
        await self.connection.commit()
        
        # Создаем индексы для производительности
        await self._create_indexes()
        
        # Инициализируем настройки
        await self._init_extended_settings()
        
        logger.info("📋 Расширенные таблицы созданы")
    
    async def _create_indexes(self):
        """🚀 Создание индексов для производительности (ФИНАЛЬНО ИСПРАВЛЕНО)"""
        
        # ТОЛЬКО индексы для СУЩЕСТВУЮЩИХ таблиц и колонок
        indexes = [
            # Основные таблицы (проверенные колонки)
            "CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages (chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)",
            
            "CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_actions_action ON user_actions (action)",
            "CREATE INDEX IF NOT EXISTS idx_user_actions_timestamp ON user_actions (timestamp)",
            
            # Обучение
            "CREATE INDEX IF NOT EXISTS idx_learning_user_id ON learning_interactions (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_learning_timestamp ON learning_interactions (timestamp)",
            
            # Триггеры
            "CREATE INDEX IF NOT EXISTS idx_triggers_active ON flexible_triggers (is_active)",
            "CREATE INDEX IF NOT EXISTS idx_triggers_global ON flexible_triggers (is_global)",
            "CREATE INDEX IF NOT EXISTS idx_triggers_type ON flexible_triggers (trigger_type)",
            "CREATE INDEX IF NOT EXISTS idx_trigger_activations_timestamp ON trigger_activations (timestamp)",
            
            # Модерация
            "CREATE INDEX IF NOT EXISTS idx_bans_user_id ON bans (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_bans_active ON bans (is_active)",
            
            "CREATE INDEX IF NOT EXISTS idx_mutes_user_id ON mutes (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_mutes_until ON mutes (mute_until)",
            "CREATE INDEX IF NOT EXISTS idx_mutes_active ON mutes (is_active)",
            
            "CREATE INDEX IF NOT EXISTS idx_warnings_user_id ON warnings (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_warnings_date ON warnings (warn_date)",
            
            "CREATE INDEX IF NOT EXISTS idx_mod_log_timestamp ON moderation_log (timestamp)",
            
            # Криптовалюты
            "CREATE INDEX IF NOT EXISTS idx_crypto_symbol ON crypto_cache (coin_symbol)",
            "CREATE INDEX IF NOT EXISTS idx_crypto_updated ON crypto_cache (last_updated)",
            "CREATE INDEX IF NOT EXISTS idx_crypto_requests_timestamp ON crypto_requests (timestamp)",
            
            # Статистика
            "CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_stats (date)",
            "CREATE INDEX IF NOT EXISTS idx_activity_date ON user_activity (date)",
            "CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity (user_id)",
            
            # Развлечения
            "CREATE INDEX IF NOT EXISTS idx_entertainment_timestamp ON entertainment_stats (timestamp)",
            
            # Система
            "CREATE INDEX IF NOT EXISTS idx_error_log_timestamp ON error_log (timestamp)"
        ]
        
        for index_sql in indexes:
            try:
                await self.connection.execute(index_sql)
            except Exception as e:
                logger.error(f"❌ Ошибка создания индекса: {e}")
        
        await self.connection.commit()
        logger.info("🚀 Индексы созданы")
    
    async def _init_extended_settings(self):
        """⚙️ Инициализация расширенных настроек (ФИНАЛЬНО ИСПРАВЛЕНО)"""
        
        # ТОЛЬКО key, value без description!
        default_settings = [
            ('db_version', '3.0'),
            ('created_at', datetime.now().isoformat()),
            ('random_messages_enabled', 'true'),
            ('random_messages_chance', '0.01'),
            ('learning_enabled', 'true'),
            ('learning_retention_days', '30'),
            ('auto_moderation_enabled', 'true'),
            ('toxicity_threshold', '0.7'),
            ('spam_detection_enabled', 'true'),
            ('profanity_filter_enabled', 'false'),
            ('max_triggers_per_user', '10'),
            ('max_triggers_per_admin', '100'),
            ('crypto_cache_ttl', '300'),
            ('entertainment_cooldown', '30')
        ]
        
        for key, value in default_settings:
            await self.connection.execute("""
                INSERT OR IGNORE INTO system_settings (key, value) 
                VALUES (?, ?)
            """, (key, value))
        
        await self.connection.commit()
        logger.info("⚙️ Расширенные настройки инициализированы")
    
    # =================== БАЗОВЫЕ ОПЕРАЦИИ ===================
    
    async def execute(self, query: str, params: tuple = ()):
        """🔧 Выполнение запроса"""
        try:
            cursor = await self.connection.execute(query, params)
            await self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            raise
    
    async def fetchone(self, query: str, params: tuple = ()):
        """📖 Получение одной записи"""
        try:
            cursor = await self.connection.execute(query, params)
            row = await cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Ошибка получения записи: {e}")
            return None
    
    async def fetchall(self, query: str, params: tuple = ()):
        """📚 Получение всех записей"""
        try:
            cursor = await self.connection.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows] if rows else []
        except Exception as e:
            logger.error(f"❌ Ошибка получения записей: {e}")
            return []
    
    # =================== РАСШИРЕННЫЕ ФУНКЦИИ ===================
    
    async def save_user(self, user_data: Dict[str, Any]) -> bool:
        """👤 Сохранение пользователя с расширенными данными"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO users 
                (id, username, first_name, last_name, language_code, is_premium, is_bot, 
                 last_seen, learning_profile, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data['id'],
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'), 
                user_data.get('language_code'),
                user_data.get('is_premium', False),
                user_data.get('is_bot', False),
                datetime.now(),
                json.dumps(user_data.get('learning_profile', {})),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения пользователя: {e}")
            return False
    
    async def save_chat(self, chat_data: Dict[str, Any]) -> bool:
        """💬 Сохранение чата с расширенными данными"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO chats
                (id, type, title, username, description, last_activity, 
                 settings, moderation_settings, random_messages_enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chat_data['id'],
                chat_data.get('type'),
                chat_data.get('title'),
                chat_data.get('username'),
                chat_data.get('description'),
                datetime.now(),
                json.dumps(chat_data.get('settings', {})),
                json.dumps(chat_data.get('moderation_settings', {})),
                chat_data.get('random_messages_enabled', False),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения чата: {e}")
            return False
    
    async def save_message(self, message_data: Dict[str, Any]) -> bool:
        """💬 Сохранение сообщения с анализом"""
        try:
            await self.connection.execute("""
                INSERT INTO messages
                (message_id, user_id, chat_id, text, message_type, has_media, media_type, 
                 sentiment_score, toxicity_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_data['message_id'],
                message_data['user_id'],
                message_data['chat_id'],
                message_data.get('text', ''),
                message_data.get('message_type', 'text'),
                message_data.get('has_media', False),
                message_data.get('media_type'),
                message_data.get('sentiment_score', 0.0),
                message_data.get('toxicity_score', 0.0),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сообщения: {e}")
            return False
    
    # =================== АДАПТИВНОЕ ОБУЧЕНИЕ ===================
    
    async def save_learning_interaction(self, user_id: int, chat_id: int, 
                                       user_message: str, bot_response: str,
                                       context_data: dict = None) -> bool:
        """🧠 Сохранение данных для обучения"""
        try:
            await self.connection.execute("""
                INSERT INTO learning_interactions
                (user_id, chat_id, user_message, bot_response, context_data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, chat_id, user_message, bot_response,
                json.dumps(context_data or {}), datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения обучения: {e}")
            return False
    
    async def get_user_learning_data(self, user_id: int) -> Dict[str, Any]:
        """🧠 Получение данных обучения пользователя"""
        try:
            # Получаем последние взаимодействия
            interactions = await self.fetchall("""
                SELECT user_message, bot_response, context_data, timestamp
                FROM learning_interactions 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            """, (user_id,))
            
            # Получаем предпочтения
            preferences = await self.fetchone("""
                SELECT preference_data, learning_data 
                FROM user_preferences 
                WHERE user_id = ?
            """, (user_id,))
            
            return {
                'recent_interactions': interactions,
                'preferences': json.loads(preferences['preference_data']) if preferences else {},
                'learning_data': json.loads(preferences['learning_data']) if preferences else {}
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных обучения: {e}")
            return {}
    
    # =================== ГИБКИЕ ТРИГГЕРЫ ===================
    
    async def save_flexible_trigger(self, trigger_data: Dict[str, Any]) -> bool:
        """⚡ Сохранение гибкого триггера"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO flexible_triggers
                (user_id, chat_id, name, trigger_type, pattern, response_data, 
                 conditions, settings, is_active, is_global, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trigger_data['user_id'],
                trigger_data.get('chat_id'),
                trigger_data['name'],
                trigger_data['trigger_type'],
                trigger_data['pattern'],
                json.dumps(trigger_data['response_data']),
                json.dumps(trigger_data.get('conditions', {})),
                json.dumps(trigger_data.get('settings', {})),
                trigger_data.get('is_active', True),
                trigger_data.get('is_global', False),
                datetime.now(),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения триггера: {e}")
            return False
    
    async def get_active_triggers(self, chat_id: int = None) -> List[Dict[str, Any]]:
        """⚡ Получение активных триггеров"""
        try:
            if chat_id:
                triggers = await self.fetchall("""
                    SELECT * FROM flexible_triggers 
                    WHERE is_active = TRUE AND (chat_id = ? OR is_global = TRUE)
                    ORDER BY is_global DESC, usage_count DESC
                """, (chat_id,))
            else:
                triggers = await self.fetchall("""
                    SELECT * FROM flexible_triggers 
                    WHERE is_active = TRUE 
                    ORDER BY is_global DESC, usage_count DESC
                """)
            
            # Парсим JSON поля
            for trigger in triggers:
                trigger['response_data'] = json.loads(trigger['response_data'])
                trigger['conditions'] = json.loads(trigger['conditions'])
                trigger['settings'] = json.loads(trigger['settings'])
            
            return triggers
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения триггеров: {e}")
            return []
    
    # =================== КАСТОМНЫЕ СЛОВА ===================
    
    async def add_custom_trigger_word(self, word: str, added_by: int) -> bool:
        """🔤 Добавление кастомного слова призыва"""
        try:
            await self.connection.execute("""
                INSERT OR IGNORE INTO custom_trigger_words (word, added_by)
                VALUES (?, ?)
            """, (word.lower(), added_by))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления слова: {e}")
            return False
    
    async def get_custom_trigger_words(self) -> List[str]:
        """🔤 Получение всех кастомных слов"""
        try:
            words = await self.fetchall("""
                SELECT word FROM custom_trigger_words 
                WHERE is_active = TRUE 
                ORDER BY usage_count DESC
            """)
            
            return [word['word'] for word in words]
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения кастомных слов: {e}")
            return []
    
    # =================== МОДЕРАЦИЯ ===================
    
    async def add_moderation_action(self, action_data: Dict[str, Any]) -> bool:
        """🛡️ Добавление действия модерации"""
        try:
            action_type = action_data['action']
            
            if action_type == 'ban':
                await self.connection.execute("""
                    INSERT INTO bans (user_id, chat_id, admin_id, reason, ban_type, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    action_data['user_id'],
                    action_data.get('chat_id'),
                    action_data['admin_id'],
                    action_data.get('reason', ''),
                    action_data.get('ban_type', 'permanent'),
                    action_data.get('expires_at')
                ))
            
            elif action_type == 'mute':
                await self.connection.execute("""
                    INSERT INTO mutes (user_id, chat_id, admin_id, reason, mute_until, mute_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    action_data['user_id'],
                    action_data['chat_id'],
                    action_data['admin_id'],
                    action_data.get('reason', ''),
                    action_data['mute_until'],
                    action_data.get('mute_type', 'full')
                ))
            
            elif action_type == 'warn':
                await self.connection.execute("""
                    INSERT INTO warnings (user_id, chat_id, admin_id, reason, severity_level)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    action_data['user_id'],
                    action_data['chat_id'],
                    action_data['admin_id'],
                    action_data.get('reason', ''),
                    action_data.get('severity_level', 1)
                ))
            
            elif action_type == 'kick':
                await self.connection.execute("""
                    INSERT INTO kicks (user_id, chat_id, admin_id, reason)
                    VALUES (?, ?, ?, ?)
                """, (
                    action_data['user_id'],
                    action_data['chat_id'],
                    action_data['admin_id'],
                    action_data.get('reason', '')
                ))
            
            # Логируем действие
            await self.connection.execute("""
                INSERT INTO moderation_log 
                (user_id, chat_id, admin_id, action, reason, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                action_data['user_id'],
                action_data.get('chat_id'),
                action_data['admin_id'],
                action_type,
                action_data.get('reason', ''),
                json.dumps(action_data.get('details', {}))
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления действия модерации: {e}")
            return False
    
    # =================== СТАТИСТИКА ===================
    
    async def get_comprehensive_user_stats(self, user_id: int) -> Dict[str, Any]:
        """📊 Полная статистика пользователя"""
        try:
            stats = {}
            
            # Основная статистика
            user_data = await self.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
            if user_data:
                stats['user_data'] = user_data
            
            # Сообщения
            message_stats = await self.fetchone("""
                SELECT 
                    COUNT(*) as total_messages,
                    AVG(LENGTH(text)) as avg_message_length,
                    COUNT(CASE WHEN DATE(timestamp) = DATE('now') THEN 1 END) as messages_today,
                    COUNT(CASE WHEN timestamp >= datetime('now', '-7 days') THEN 1 END) as messages_week
                FROM messages WHERE user_id = ?
            """, (user_id,))
            
            if message_stats:
                stats['messages'] = message_stats
            
            # Действия
            action_stats = await self.fetchall("""
                SELECT action, COUNT(*) as count 
                FROM user_actions 
                WHERE user_id = ? 
                GROUP BY action 
                ORDER BY count DESC
            """, (user_id,))
            
            stats['actions'] = {row['action']: row['count'] for row in action_stats}
            
            # Обучение
            learning_stats = await self.fetchone("""
                SELECT 
                    COUNT(*) as total_interactions,
                    AVG(satisfaction_score) as avg_satisfaction,
                    COUNT(CASE WHEN was_helpful = TRUE THEN 1 END) as helpful_responses
                FROM learning_interactions WHERE user_id = ?
            """, (user_id,))
            
            if learning_stats:
                stats['learning'] = learning_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    # =================== ЗАКРЫТИЕ ===================
    
    async def close(self):
        """🚪 Закрытие соединения"""
        if self.connection:
            await self.connection.close()
            self.initialized = False
            logger.info("💾 Расширенная база данных закрыта")
    
    def __del__(self):
        """🗑️ Деструктор"""
        if self.connection and self.initialized:
            try:
                asyncio.create_task(self.close())
            except:
                pass