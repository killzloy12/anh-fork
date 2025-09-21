#!/usr/bin/env python3
"""
🎛️ HANDLERS v3.0 - ГРУБЫЙ РЕЖИМ
🔥 ИСПРАВЛЕННЫЕ обработчики с жестким контролем

ИСПРАВЛЕНО:
• Работа ТОЛЬКО в разрешенных чатах
• НЕ отвечает на каждое сообщение  
• Отвечает ТОЛЬКО при обращении, командах, реплеях
• Логирует ВСЕ сообщения чата
• Редкая самостоятельная активность
"""

import logging
import re
import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Sticker
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

# Глобальные переменные для управления активностью
last_activity_time = {}
bot_trigger_words = ["бот", "bot", "робот", "помощник", "assistant", "эй", "слушай"]

def register_all_handlers(dp, modules):
    """🎛️ Регистрация ВСЕХ обработчиков в грубом режиме"""
    
    router = Router()
    
    # Получаем информацию о боте для упоминаний
    bot_info = None
    
    async def get_bot_info():
        nonlocal bot_info
        try:
            bot_info = await modules['bot'].get_me()
            logger.info(f"🤖 Бот: @{bot_info.username} ({bot_info.first_name})")
        except Exception as e:
            logger.error(f"❌ Не удалось получить информацию о боте: {e}")
    
    asyncio.create_task(get_bot_info())
    
    # ================= ФИЛЬТР ДОСТУПА К ЧАТАМ =================
    
    async def check_chat_access(message: Message) -> bool:
        """🔒 Проверка доступа к чату"""
        config = modules['config']
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Админы имеют доступ везде
        if user_id in config.bot.admin_ids:
            return True
            
        # Если список разрешенных чатов пуст - разрешаем все
        if not config.bot.allowed_chat_ids:
            return True
            
        # Проверяем, есть ли чат в списке разрешенных
        if chat_id not in config.bot.allowed_chat_ids:
            logger.info(f"🚫 Доступ запрещен: чат {chat_id} не в списке разрешенных")
            return False
            
        return True
    
    # ================= ЛОГИРОВАНИЕ ВСЕХ СООБЩЕНИЙ =================
    
    async def log_message(message: Message):
        """📝 Логирование всех сообщений для обучения"""
        try:
            if modules.get('db'):
                await modules['db'].log_message(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    username=message.from_user.username or '',
                    full_name=message.from_user.full_name or '',
                    text=message.text or '',
                    message_type='text',
                    timestamp=datetime.now()
                )
                
            # Трекинг аналитики
            if modules.get('analytics'):
                await modules['analytics'].track_user_action(
                    message.from_user.id, 
                    message.chat.id, 
                    'message_sent',
                    {
                        'text_length': len(message.text) if message.text else 0,
                        'chat_type': message.chat.type,
                        'has_reply': bool(message.reply_to_message)
                    }
                )
        except Exception as e:
            logger.error(f"❌ Ошибка логирования: {e}")
    
    # ================= ОСНОВНЫЕ КОМАНДЫ =================
    
    @router.message(CommandStart())
    async def start_handler(message: Message):
        """🚀 Команда /start"""
        if not await check_chat_access(message):
            return
            
        await log_message(message)
        
        user = message.from_user
        chat_type_text = "личных сообщениях" if message.chat.type == 'private' else f"чате **{message.chat.title or 'Неизвестный'}**"
        
        response = (
            f"💀 **Грубый бот v3.0 запущен**\n\n"
            f"Привет, **{user.first_name}**!\n"
            f"Работаю в {chat_type_text}\n\n"
            f"🔥 **Особенности:**\n"
            f"• Отвечаю ТОЛЬКО при обращении\n"
            f"• Логирую ВСЕ сообщения\n"
            f"• Редко проявляю активность\n"
            f"• Жесткие ограничения доступа\n\n"
            f"💡 /help - список команд"
        )
        
        await message.reply(response)
        logger.info(f"✅ /start: {user.id} в чате {message.chat.id}")
    
    @router.message(Command('help'))
    async def help_handler(message: Message):
        """📖 Справка"""
        if not await check_chat_access(message):
            return
            
        await log_message(message)
        
        help_text = (
            "📖 **Справка по командам**\n\n"
            "🤖 **Основные:**\n"
            "/start - Запуск бота\n"
            "/help - Эта справка\n"
            "/ai [текст] - AI помощник\n"
            "/stats - Статистика\n"
            "/about - О боте\n\n"
            "🎯 **Как меня вызвать:**\n"
            "• Напиши 'бот' в сообщении\n"
            "• Ответь на мое сообщение\n"
            "• Используй команды\n\n"
            "💀 **Работаю ТОЛЬКО в разрешенных чатах**"
        )
        
        await message.reply(help_text)
    
    @router.message(Command('about'))
    async def about_handler(message: Message):
        """ℹ️ О боте"""
        if not await check_chat_access(message):
            return
            
        await log_message(message)
        
        active_modules = sum(1 for m in modules.values() if m is not None and m != modules.get('config') and m != modules.get('bot') and m != modules.get('db'))
        
        about_text = (
            "💀 **Enhanced Telegram Bot v3.0**\n"
            "**Грубый режим**\n\n"
            "🎯 **Особенности:**\n"
            "• Работа только в разрешенных чатах\n"
            "• Логирование всех сообщений\n"
            "• Ответы только при обращении\n"
            "• Редкая самостоятельная активность\n"
            "• Жесткий контроль доступа\n\n"
            f"🧩 **Активных модулей:** {active_modules}\n"
            f"⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}"
        )
        
        await message.reply(about_text)
    
    @router.message(Command('stats'))
    async def stats_handler(message: Message):
        """📊 Статистика"""
        if not await check_chat_access(message):
            return
            
        await log_message(message)
        
        # Получаем статистику из БД
        stats_text = "📊 **Ваша статистика**\n\n"
        
        try:
            if modules.get('db'):
                # Подсчет сообщений пользователя
                user_stats = await modules['db'].get_user_stats(message.from_user.id)
                stats_text += f"📝 **Сообщений отправлено:** {user_stats.get('total_messages', 0)}\n"
                stats_text += f"🗓️ **Активен с:** {user_stats.get('first_seen', 'неизвестно')}\n"
                stats_text += f"⏰ **Последняя активность:** {user_stats.get('last_seen', 'сейчас')}\n"
            else:
                stats_text += "❌ База данных недоступна"
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            stats_text += "❌ Ошибка получения статистики"
        
        await message.reply(stats_text)
    
    @router.message(Command('ai'))
    async def ai_handler(message: Message):
        """🧠 AI помощник"""
        if not await check_chat_access(message):
            return
            
        await log_message(message)
        
        if not modules.get('ai'):
            await message.reply("❌ AI модуль отключен")
            return
        
        user_message = message.text[4:].strip()
        if not user_message:
            await message.reply(
                "💡 **Использование:**\n"
                "/ai [ваш вопрос]\n\n"
                "**Пример:**\n"
                "/ai Как дела?"
            )
            return
        
        try:
            # Генерируем ответ через AI
            response = await modules['ai'].generate_response(
                user_message, 
                message.from_user.id,
                {'chat_type': message.chat.type}
            )
            
            await message.reply(response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка AI: {e}")
            await message.reply("❌ Ошибка обработки AI запроса")
    
    # ================= ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =================
    
    @router.message(F.text)
    async def text_message_handler(message: Message):
        """📝 Обработка всех текстовых сообщений"""
        
        # ВСЕГДА логируем сообщение
        await log_message(message)
        
        # Проверяем доступ к чату
        if not await check_chat_access(message):
            return
        
        # Пропускаем команды (они обрабатываются отдельно)
        if message.text.startswith('/'):
            return
            
        text_lower = message.text.lower()
        should_respond = False
        
        # 1. Проверяем, это реплай на сообщение бота
        if message.reply_to_message and message.reply_to_message.from_user.id == modules['bot'].id:
            should_respond = True
            await handle_reply_to_bot(message, modules)
            return
        
        # 2. Проверяем обращение к боту по ключевым словам
        for trigger_word in bot_trigger_words:
            if trigger_word in text_lower:
                should_respond = True
                break
        
        # 3. Проверяем упоминание бота (@username)
        if bot_info and f'@{bot_info.username.lower()}' in text_lower:
            should_respond = True
        
        # 4. Проверяем имя бота
        if bot_info and bot_info.first_name.lower() in text_lower:
            should_respond = True
        
        # 5. В личных сообщениях всегда отвечаем
        if message.chat.type == 'private':
            should_respond = True
        
        if should_respond:
            await handle_bot_mention(message, modules)
        
        # 6. Редкая самостоятельная активность
        await handle_random_activity(message, modules)
    
    # ================= ОБРАБОТКА РЕПЛЕЕВ НА БОТА =================
    
    async def handle_reply_to_bot(message: Message, modules):
        """💬 Обработка реплея на сообщение бота"""
        try:
            logger.info(f"💬 Реплей на бота от {message.from_user.id}: {message.text}")
            
            if modules.get('ai'):
                # Формируем контекст с предыдущим сообщением
                context_message = f"Контекст: {message.reply_to_message.text}\n\nОтвет пользователя: {message.text}"
                
                response = await modules['ai'].generate_response(
                    context_message,
                    message.from_user.id,
                    {'is_reply': True, 'chat_type': message.chat.type}
                )
            else:
                responses = [
                    "Понял тебя",
                    "Ясно", 
                    "Записал",
                    "Окей",
                    "Учту"
                ]
                response = random.choice(responses)
            
            await message.reply(response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки реплея: {e}")
    
    # ================= ОБРАБОТКА ОБРАЩЕНИЙ К БОТУ =================
    
    async def handle_bot_mention(message: Message, modules):
        """🎯 Обработка обращения к боту"""
        try:
            logger.info(f"🎯 Обращение к боту от {message.from_user.id}: {message.text}")
            
            if modules.get('ai'):
                response = await modules['ai'].generate_response(
                    message.text,
                    message.from_user.id,
                    {'is_mention': True, 'chat_type': message.chat.type}
                )
            else:
                responses = [
                    "Что надо?",
                    "Слушаю",
                    "Говори", 
                    "Че?",
                    "Ну?",
                    "И что?",
                    "Да?"
                ]
                response = random.choice(responses)
            
            await message.reply(response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки обращения: {e}")
    
    # ================= РЕДКАЯ САМОСТОЯТЕЛЬНАЯ АКТИВНОСТЬ =================
    
    async def handle_random_activity(message: Message, modules):
        """🎲 Редкая самостоятельная активность бота"""
        try:
            chat_id = message.chat.id
            config = modules['config']
            
            # Очень низкий шанс активности (0.1%)
            if random.random() > 0.999:
                return
            
            # Проверяем, не было ли недавно активности в этом чате
            now = datetime.now()
            if chat_id in last_activity_time:
                if now - last_activity_time[chat_id] < timedelta(hours=2):
                    return  # Слишком рано для активности
            
            last_activity_time[chat_id] = now
            
            random_responses = [
                "И что дальше?",
                "Ну и?", 
                "Скучно...",
                "Что-то тихо тут",
                "Все спят?",
                "Кто тут?",
                "М-да..."
            ]
            
            response = random.choice(random_responses)
            
            # Задержка перед отправкой (от 5 до 30 секунд)
            await asyncio.sleep(random.randint(5, 30))
            
            await modules['bot'].send_message(chat_id, response)
            logger.info(f"🎲 Самостоятельная активность в чате {chat_id}: {response}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка самостоятельной активности: {e}")
    
    # ================= ОБРАБОТКА СТИКЕРОВ =================
    
    @router.message(F.sticker)
    async def sticker_handler(message: Message):
        """🎭 Обработка стикеров"""
        if not await check_chat_access(message):
            return
        
        # Логируем стикер
        try:
            if modules.get('db'):
                await modules['db'].log_message(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    username=message.from_user.username or '',
                    full_name=message.from_user.full_name or '',
                    text=f"[STICKER: {message.sticker.emoji}]",
                    message_type='sticker',
                    timestamp=datetime.now()
                )
        except Exception as e:
            logger.error(f"❌ Ошибка логирования стикера: {e}")
        
        # Иногда реагируем на стикеры
        if random.random() < 0.05:  # 5% шанс
            sticker_responses = ["👍", "👎", "🤔", "😄", "🙄"]
            response = random.choice(sticker_responses)
            await message.reply(response)
    
    # ================= АДМИНИСТРАТИВНЫЕ КОМАНДЫ =================
    
    @router.message(Command('admin'))
    async def admin_handler(message: Message):
        """👑 Административная панель"""
        user_id = message.from_user.id
        if user_id not in modules['config'].bot.admin_ids:
            return
        
        if message.chat.type != 'private':
            await message.reply("🔒 Админ-команды только в ЛС")
            return
        
        admin_text = (
            "👑 **Админ панель v3.0**\n\n"
            "📊 /logs - Экспорт логов\n"
            "🔄 /reload - Перезагрузить триггеры\n"
            "📈 /system_stats - Системная статистика\n"
            "🗑️ /clear_logs - Очистить логи\n"
            "⚙️ /settings - Настройки бота\n\n"
            "💀 **Грубый режим активен**"
        )
        
        await message.reply(admin_text)
    
    @router.message(Command('logs'))
    async def logs_handler(message: Message):
        """📊 Экспорт логов (только админы)"""
        user_id = message.from_user.id
        if user_id not in modules['config'].bot.admin_ids:
            return
            
        try:
            if modules.get('db'):
                logs = await modules['db'].export_recent_logs(limit=1000)
                
                # Создаем файл с логами
                log_text = "# Экспорт логов чата\n\n"
                for log in logs:
                    log_text += f"[{log['timestamp']}] {log['username']} ({log['user_id']}): {log['text']}\n"
                
                # Отправляем как документ
                from io import StringIO
                log_file = StringIO(log_text)
                log_file.name = f"chat_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                await message.reply_document(
                    document=log_file,
                    caption="📊 Экспорт логов чата"
                )
            else:
                await message.reply("❌ База данных недоступна")
                
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта логов: {e}")
            await message.reply("❌ Ошибка экспорта логов")
    
    # Регистрируем роутер
    dp.include_router(router)
    
    logger.info("🎛️ Грубые обработчики v3.0 зарегистрированы")
    

def register_basic_handlers(dp, modules):
    """🔧 Базовые обработчики (если модули недоступны)"""
    register_all_handlers(dp, modules)


# ================= ЭКСПОРТ =================

__all__ = ["register_all_handlers", "register_basic_handlers"]