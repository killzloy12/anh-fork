#!/usr/bin/env python3
"""
💾 DATABASE SERVICE v3.0 - ПОЛНАЯ РЕАЛИЗАЦИЯ
🔥 Все таблицы для модерации, аналитики и статистики

ТАБЛИЦЫ:
• users - Пользователи с полной инфой
• chats - Чаты с активностью
• messages - Сообщения с трекингом
• user_actions - Действия пользователей
• bans - Баны модерации
• mutes - Муты модерации  
• warnings - Предупреждения
• crypto_cache - Кэш криптовалют
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
    """💾 Полный сервис базы данных"""
    
    def __init__(self, config):
        self.config = config
        self.db_path = Path(config.path)
        self.connection = None
        self.initialized = False
        
        # Создаем директорию если нужно
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """🚀 Инициализация базы данных"""
        try:
            # Подключаемся к БД
            self.connection = await aiosqlite.connect(
                self.db_path,
                timeout=30.0
            )
            
            # Включаем WAL режим для лучшей производительности
            if self.config.wal_mode:
                await self.connection.execute("PRAGMA journal_mode=WAL")
                await self.connection.execute("PRAGMA synchronous=NORMAL")
                await self.connection.execute("PRAGMA cache_size=10000")
                await self.connection.execute("PRAGMA temp_store=memory")
            
            # Создаем все таблицы
            await self._create_tables()
            
            self.initialized = True
            logger.info("💾 Database Service инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    async def _create_tables(self):
        """📋 Создание всех необходимых таблиц"""
        
        tables = [
            # ОСНОВНЫЕ ТАБЛИЦЫ
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
                settings TEXT,
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (chat_id) REFERENCES chats (id),
                INDEX idx_messages_user_id (user_id),
                INDEX idx_messages_chat_id (chat_id),
                INDEX idx_messages_timestamp (timestamp)
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
                FOREIGN KEY (chat_id) REFERENCES chats (id),
                INDEX idx_actions_user_id (user_id),
                INDEX idx_actions_action (action),
                INDEX idx_actions_timestamp (timestamp)
            )
            """,
            
            # МОДЕРАЦИЯ
            """
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                ban_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                unban_date DATETIME,
                is_global BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES users (id),
                INDEX idx_bans_user_id (user_id),
                INDEX idx_bans_active (is_active)
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
                is_active BOOLEAN DEFAULT TRUE,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES users (id),
                INDEX idx_mutes_user_id (user_id),
                INDEX idx_mutes_until (mute_until),
                INDEX idx_mutes_active (is_active)
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
                is_active BOOLEAN DEFAULT TRUE,
                
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES users (id),
                INDEX idx_warnings_user_id (user_id),
                INDEX idx_warnings_date (warn_date)
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_mod_log_action (action),
                INDEX idx_mod_log_timestamp (timestamp)
            )
            """,
            
            # КРИПТОВАЛЮТЫ
            """
            CREATE TABLE IF NOT EXISTS crypto_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin_id TEXT NOT NULL,
                coin_symbol TEXT NOT NULL,
                price_data TEXT NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(coin_id),
                INDEX idx_crypto_symbol (coin_symbol),
                INDEX idx_crypto_updated (last_updated)
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_crypto_req_user (user_id),
                INDEX idx_crypto_req_coin (coin_found)
            )
            """,
            
            # АНАЛИТИКА
            """
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                chat_id INTEGER,
                total_messages INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                ai_requests INTEGER DEFAULT 0,
                crypto_requests INTEGER DEFAULT 0,
                moderation_actions INTEGER DEFAULT 0,
                
                UNIQUE(date, chat_id),
                INDEX idx_daily_date (date)
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
                stickers_sent INTEGER DEFAULT 0,
                
                UNIQUE(user_id, chat_id, date),
                INDEX idx_activity_date (date),
                INDEX idx_activity_user (user_id)
            )
            """,
            
            # ТРИГГЕРЫ
            """
            CREATE TABLE IF NOT EXISTS triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER,
                name TEXT NOT NULL,
                pattern TEXT NOT NULL,
                response TEXT NOT NULL,
                trigger_type TEXT DEFAULT 'contains',
                is_active BOOLEAN DEFAULT TRUE,
                is_global BOOLEAN DEFAULT FALSE,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(user_id, chat_id, name),
                INDEX idx_triggers_active (is_active),
                INDEX idx_triggers_global (is_global)
            )
            """,
            
            # СИСТЕМА
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                INDEX idx_error_type (error_type),
                INDEX idx_error_timestamp (timestamp)
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
        logger.info("📋 Таблицы созданы/обновлены")
        
        # Создаем начальные настройки
        await self._init_system_settings()
    
    async def _init_system_settings(self):
        """⚙️ Инициализация системных настроек"""
        
        default_settings = [
            ('db_version', '3.0'),
            ('created_at', datetime.now().isoformat()),
            ('total_users', '0'),
            ('total_messages', '0'),
            ('bot_started_at', datetime.now().isoformat())
        ]
        
        for key, value in default_settings:
            await self.connection.execute(
                "INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        
        await self.connection.commit()
    
    # =================== ОСНОВНЫЕ ОПЕРАЦИИ ===================
    
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
    
    # =================== ПОЛЬЗОВАТЕЛИ ===================
    
    async def save_user(self, user_data: Dict[str, Any]) -> bool:
        """👤 Сохранение пользователя"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO users 
                (id, username, first_name, last_name, language_code, is_premium, is_bot, last_seen, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data['id'],
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'), 
                user_data.get('language_code'),
                user_data.get('is_premium', False),
                user_data.get('is_bot', False),
                datetime.now(),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения пользователя: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """👤 Получение пользователя"""
        return await self.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
    
    async def update_user_stats(self, user_id: int, **kwargs):
        """📊 Обновление статистики пользователя"""
        try:
            set_clauses = []
            params = []
            
            for key, value in kwargs.items():
                if key in ['total_messages', 'total_ai_requests', 'total_crypto_requests', 'reputation_score']:
                    set_clauses.append(f"{key} = {key} + ?")
                    params.append(value)
            
            if set_clauses:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(set_clauses)}, updated_at = ? WHERE id = ?"
                params.insert(-1, datetime.now())
                
                await self.connection.execute(query, params)
                await self.connection.commit()
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статистики пользователя: {e}")
    
    # =================== ЧАТЫ ===================
    
    async def save_chat(self, chat_data: Dict[str, Any]) -> bool:
        """💬 Сохранение чата"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO chats
                (id, type, title, username, description, last_activity, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                chat_data['id'],
                chat_data.get('type'),
                chat_data.get('title'),
                chat_data.get('username'),
                chat_data.get('description'),
                datetime.now(),
                datetime.now()
            ))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения чата: {e}")
            return False
    
    # =================== СООБЩЕНИЯ ===================
    
    async def save_message(self, message_data: Dict[str, Any]) -> bool:
        """💬 Сохранение сообщения"""
        try:
            await self.connection.execute("""
                INSERT INTO messages
                (message_id, user_id, chat_id, text, message_type, has_media, media_type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_data['message_id'],
                message_data['user_id'],
                message_data['chat_id'],
                message_data.get('text', ''),
                message_data.get('message_type', 'text'),
                message_data.get('has_media', False),
                message_data.get('media_type'),
                datetime.now()
            ))
            
            await self.connection.commit()
            
            # Обновляем статистику пользователя
            await self.update_user_stats(message_data['user_id'], total_messages=1)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения сообщения: {e}")
            return False
    
    # =================== АНАЛИТИКА ===================
    
    async def track_user_action(self, user_id: int, chat_id: int, action: str, data: Dict = None):
        """📊 Трекинг действий пользователя"""
        try:
            await self.connection.execute("""
                INSERT INTO user_actions (user_id, chat_id, action, action_data, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id, chat_id, action, 
                json.dumps(data) if data else None,
                datetime.now()
            ))
            
            await self.connection.commit()
            
        except Exception as e:
            logger.error(f"❌ Ошибка трекинга действия: {e}")
    
    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """📊 Статистика пользователя"""
        try:
            user_data = await self.get_user(user_id)
            if not user_data:
                return {}
            
            today = datetime.now().date()
            week_ago = datetime.now() - timedelta(days=7)
            
            # Сообщения за сегодня
            messages_today = await self.fetchone("""
                SELECT COUNT(*) as count FROM messages 
                WHERE user_id = ? AND DATE(timestamp) = ?
            """, (user_id, today))
            
            # Сообщения за неделю  
            messages_week = await self.fetchone("""
                SELECT COUNT(*) as count FROM messages
                WHERE user_id = ? AND timestamp >= ?
            """, (user_id, week_ago))
            
            # AI запросы за сегодня
            ai_today = await self.fetchone("""
                SELECT COUNT(*) as count FROM user_actions
                WHERE user_id = ? AND action = 'ai_request' AND DATE(timestamp) = ?
            """, (user_id, today))
            
            # Средняя длина сообщений
            avg_length = await self.fetchone("""
                SELECT AVG(LENGTH(text)) as avg_len FROM messages
                WHERE user_id = ? AND text != ''
            """, (user_id,))
            
            return {
                'total_messages': user_data.get('total_messages', 0),
                'messages_today': messages_today['count'] if messages_today else 0,
                'messages_week': messages_week['count'] if messages_week else 0,
                'ai_requests': user_data.get('total_ai_requests', 0),
                'ai_requests_today': ai_today['count'] if ai_today else 0,
                'crypto_requests': user_data.get('total_crypto_requests', 0),
                'avg_length': int(avg_length['avg_len']) if avg_length and avg_length['avg_len'] else 0,
                'first_seen': user_data.get('first_seen', 'Неизвестно'),
                'last_activity': user_data.get('last_seen', 'Сейчас'),
                'reputation_score': user_data.get('reputation_score', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    # =================== МОДЕРАЦИЯ ===================
    
    async def add_ban(self, user_id: int, admin_id: int, reason: str, chat_id: int = None) -> bool:
        """🚫 Добавление бана"""
        try:
            await self.connection.execute("""
                INSERT INTO bans (user_id, chat_id, admin_id, reason, ban_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, chat_id, admin_id, reason, datetime.now(), True))
            
            # Обновляем статус пользователя
            await self.connection.execute("""
                UPDATE users SET is_banned = ?, ban_reason = ? WHERE id = ?
            """, (True, reason, user_id))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления бана: {e}")
            return False
    
    async def remove_ban(self, user_id: int) -> bool:
        """✅ Снятие бана"""
        try:
            await self.connection.execute("""
                UPDATE bans SET is_active = ?, unban_date = ? WHERE user_id = ? AND is_active = ?
            """, (False, datetime.now(), user_id, True))
            
            await self.connection.execute("""
                UPDATE users SET is_banned = ?, ban_reason = ? WHERE id = ?
            """, (False, None, user_id))
            
            await self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка снятия бана: {e}")
            return False
    
    # =================== ЗАКРЫТИЕ ===================
    
    async def close(self):
        """🚪 Закрытие соединения"""
        if self.connection:
            await self.connection.close()
            self.initialized = False
            logger.info("💾 База данных закрыта")
    
    def __del__(self):
        """🗑️ Деструктор"""
        if self.connection and self.initialized:
            try:
                asyncio.create_task(self.close())
            except:
                pass