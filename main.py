#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart  
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    bot_token: str
    admin_ids: List[int]

    def __post_init__(self):
        if not self.bot_token:
            raise ValueError("❌ BOT_TOKEN обязателен")

class EnhancedTelegramBot:
    def __init__(self):
        self.config = self._load_config()
        self.bot = Bot(token=self.config.bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.stats = {'messages': 0, 'users': set(), 'start_time': datetime.now()}
        self._register_handlers()
        logger.info("🚀 Enhanced Telegram Bot v3.0 готов к работе")

    def _load_config(self):
        bot_token = os.getenv('BOT_TOKEN')
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        try:
            admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
        except ValueError:
            admin_ids = []
        return BotConfig(bot_token=bot_token, admin_ids=admin_ids)

    def _register_handlers(self):
        self.dp.message(CommandStart())(self._handle_start)
        self.dp.message(Command('help'))(self._handle_help)
        self.dp.message(Command('about'))(self._handle_about)
        self.dp.message(Command('stats'))(self._handle_stats)
        self.dp.message(Command('ping'))(self._handle_ping)
        self.dp.message()(self._handle_all_messages)

    async def _handle_start(self, message: Message):
        user = message.from_user
        self.stats['users'].add(user.id)
        welcome = f"""🚀 <b>Добро пожаловать, {user.first_name}!</b>

🤖 <b>Enhanced Telegram Bot v3.0 - Production Ready</b>

📋 <b>Команды:</b>
• /help - Справка
• /about - О боте  
• /stats - Статистика
• /ping - Проверить отклик

💡 <i>Полностью рабочий бот готов к использованию!</i>"""
        await message.answer(welcome, parse_mode="HTML")
        logger.info(f"Новый пользователь: {user.first_name} [{user.id}]")

    async def _handle_help(self, message: Message):
        help_text = """📚 <b>Справка Enhanced Bot v3.0</b>

🎯 <b>Команды:</b>
• /start - Приветствие
• /help - Эта справка
• /about - Информация о боте
• /stats - Статистика использования
• /ping - Проверить отклик

🔥 <b>Особенности:</b>
• Production-ready архитектура
• Comprehensive logging
• Error handling
• Statistics tracking

📖 github.com/killzloy12/anh-fork"""
        await message.answer(help_text, parse_mode="HTML")

    async def _handle_about(self, message: Message):
        uptime = datetime.now() - self.stats['start_time']
        about_text = f"""🚀 <b>Enhanced Telegram Bot v3.0</b>

📊 <b>Статистика:</b>
• Сообщений: {self.stats['messages']:,}
• Пользователей: {len(self.stats['users']):,}
• Время работы: {uptime.days}д {uptime.seconds//3600}ч

👨‍💻 <b>Разработчик:</b> @killzloy12
🔗 <b>GitHub:</b> github.com/killzloy12/anh-fork
📊 <b>Версия:</b> 3.0.0

⭐ Поставьте звезду на GitHub!"""
        await message.answer(about_text, parse_mode="HTML")

    async def _handle_stats(self, message: Message):
        uptime = datetime.now() - self.stats['start_time']
        stats_text = f"""📊 <b>Статистика бота</b>

💬 Сообщений обработано: {self.stats['messages']:,}
👥 Уникальных пользователей: {len(self.stats['users']):,}
⏱️ Время работы: {uptime.days}д {uptime.seconds//3600}ч
🔥 Статус: Онлайн

👤 Ваш ID: <code>{message.from_user.id}</code>"""
        await message.answer(stats_text, parse_mode="HTML")

    async def _handle_ping(self, message: Message):
        start = datetime.now()
        sent = await message.answer("🏓 Понг!")
        latency = (datetime.now() - start).total_seconds() * 1000
        await sent.edit_text(f"🏓 Понг! Задержка: {latency:.1f}ms\n✅ Бот работает исправно")

    async def _handle_all_messages(self, message: Message):
        self.stats['messages'] += 1
        self.stats['users'].add(message.from_user.id)
        if message.text and any(word in message.text.lower() for word in ['привет', 'hello']):
            await message.answer(f"👋 Привет, {message.from_user.first_name}! Я Enhanced Bot v3.0!")

    async def start(self):
        try:
            os.makedirs('data/logs', exist_ok=True)
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Подключен как @{bot_info.username}")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            await self.bot.session.close()

if __name__ == '__main__':
    try:
        bot = EnhancedTelegramBot()
        asyncio.run(bot.start())
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        print("💡 Добавьте BOT_TOKEN в .env файл")
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
