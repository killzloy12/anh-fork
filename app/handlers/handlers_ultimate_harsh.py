#!/usr/bin/env python3
"""
💀 HANDLERS v3.0 - ГРУБЫЙ БОТ
🔥 Максимально жесткие обработчики

ИСПРАВЛЕНИЯ:
• ❌ Убрано "Бот:" в начале ответов
• 💀 МАКСИМАЛЬНО ГРУБЫЙ стиль 
• ❌ Убрано "Думаю..." перед ответами
• 🔒 Админка ТОЛЬКО в ЛС для админов
• 📝 ID разрешенных чатов прописаны
• 💬 ВСЕ ответы только РЕПЛАЕМ
• 🎯 Ответы на @ и команды РЕПЛАЕМ
"""

import logging
import re
import asyncio
import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Sticker
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

# РАЗРЕШЕННЫЕ ЧАТЫ (ID прописаны жестко)
ALLOWED_CHAT_IDS = []  # Будет загружено из конфига


def register_all_handlers(dp, modules):
    """💀 Регистрация ГРУБЫХ обработчиков"""
    
    global ALLOWED_CHAT_IDS
    
    router = Router()
    
    # Загружаем разрешенные чаты из конфига
    if modules.get('config') and hasattr(modules['config'].bot, 'allowed_chat_ids'):
        ALLOWED_CHAT_IDS = modules['config'].bot.allowed_chat_ids
        print(f"💀 БОТ РАБОТАЕТ ТОЛЬКО В ЧАТАХ: {ALLOWED_CHAT_IDS}")
    
    # Получаем информацию о боте
    bot_info = None
    
    async def get_bot_info():
        nonlocal bot_info
        try:
            bot_info = await modules['bot'].get_me()
        except:
            pass
    
    asyncio.create_task(get_bot_info())
    
    # =================== ОСНОВНЫЕ КОМАНДЫ ===================
    
    @router.message(CommandStart())
    async def start_handler(message: Message):
        user = message.from_user
        chat_id = message.chat.id
        
        # ЖЕСТКАЯ ПРОВЕРКА ЧАТОВ
        if not check_chat_allowed(chat_id):
            await message.reply("Чат не поддерживается.")
            return
        
        # В ЛС ТОЛЬКО АДМИНЫ
        if message.chat.type == 'private':
            if user.id not in modules['config'].bot.admin_ids:
                await message.reply(f"Бот только для групп.\nДобавь в чат: @{bot_info.username if bot_info else 'bot'}")
                return
        
        await save_user_and_message(message, modules)
        
        if message.chat.type == 'private':
            # АДМИНСКАЯ ПАНЕЛЬ В ЛС
            welcome_text = (
                f"<b>БОТ v3.0 - АДМИНКА</b>\n\n"
                f"Админ: {user.first_name}\n\n"
                f"<b>Управление:</b>\n"
                f"/moderation - Модерация\n"
                f"/triggers - Триггеры\n" 
                f"/permissions - Доступ\n"
                f"/chats - Список чатов\n"
                f"/stats - Статистика\n"
                f"/status - Статус системы\n\n"
                f"<b>Разрешенные чаты:</b>\n"
            )
            
            # Добавляем список чатов
            for chat_id in ALLOWED_CHAT_IDS:
                welcome_text += f"• {chat_id}\n"
                
        else:
            # ДЛЯ ГРУПП - КОРОТКОЕ ПРИВЕТСТВИЕ
            welcome_text = (
                f"<b>БОТ v3.0</b>\n\n"
                f"{user.first_name}, работаю тут.\n\n"
                f"/help - команды"
            )
        
        await message.reply(welcome_text)
        
        if modules.get('analytics'):
            await modules['analytics'].track_user_action(user.id, chat_id, 'start_command')
    
    @router.message(Command('help'))
    async def help_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
        
        if message.chat.type == 'private':
            if message.from_user.id not in modules['config'].bot.admin_ids:
                await message.reply("Бот только для групп.")
                return
            # АДМИНСКАЯ СПРАВКА
            help_text = (
                "<b>АДМИНКА</b>\n\n"
                "<b>Управление:</b>\n"
                "/moderation - Настройки модерации\n"
                "/permissions - Настройки доступа\n"
                "/triggers - Управление триггерами\n"
                "/chats - ID разрешенных чатов\n\n"
                "<b>Триггеры:</b>\n"
                "/trigger_add [имя] [паттерн] [ответ] [тип]\n"
                "/trigger_list - Список\n"
                "/trigger_del [имя] - Удалить\n\n"
                "<b>Статистика:</b>\n"
                "/stats - Общая статистика\n"
                "/dashboard - Детали\n"
                "/export - Экспорт\n\n"
                "<b>Система:</b>\n"
                "/status - Статус модулей"
            )
        else:
            # ОБЫЧНАЯ СПРАВКА БЕЗ АДМИНКИ
            help_text = (
                "<b>БОТ v3.0</b>\n\n"
                "<b>Команды:</b>\n"
                "/ai - AI помощник\n"
                "/crypto - Криптовалюты\n"
                "/stats - Твоя статистика\n\n"
                "<b>Умные ответы:</b>\n"
                f"@{bot_info.username if bot_info else 'bot'} - упоминание\n"
                "Ответь на мое сообщение\n"
                "Напиши 'бот' в сообщении"
            )
            
        await message.reply(help_text)
    
    @router.message(Command('chats'))
    async def chats_handler(message: Message):
        # ТОЛЬКО АДМИНЫ В ЛС
        if message.chat.type != 'private' or message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Команда только для админов в ЛС.")
            return
        
        chats_text = "<b>РАЗРЕШЕННЫЕ ЧАТЫ:</b>\n\n"
        
        for i, chat_id in enumerate(ALLOWED_CHAT_IDS, 1):
            # Пытаемся получить инфо о чате
            try:
                chat_info = await modules['bot'].get_chat(chat_id)
                chat_name = chat_info.title or chat_info.first_name or "Неизвестно"
                chats_text += f"{i}. <code>{chat_id}</code>\n   {chat_name}\n\n"
            except:
                chats_text += f"{i}. <code>{chat_id}</code>\n   (Недоступно)\n\n"
        
        if not ALLOWED_CHAT_IDS:
            chats_text += "Нет разрешенных чатов.\nНастрой ALLOWED_CHAT_IDS в .env"
        
        await message.reply(chats_text)
    
    @router.message(Command('about'))
    async def about_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
            
        about_text = (
            "<b>БОТ v3.0 - ГРУБАЯ ВЕРСИЯ</b>\n\n"
            "Жесткий бот без соплей.\n\n"
            "<b>Технологии:</b>\n"
            "• Python 3.11 + aiogram 3.8\n"
            "• AI: GPT-4 + Claude\n"
            "• SQLite с WAL\n\n"
            "<b>Особенности:</b>\n"
            "• Работает только в разрешенных чатах\n"
            "• Админка только в ЛС\n"
            "• Грубые короткие ответы\n"
            "• Жесткая модерация\n"
            "• Все ответы реплаем\n\n"
            f"<b>Время:</b> {datetime.now().strftime('%H:%M:%S')}\n"
            "<b>Версия:</b> 3.0 Грубая"
        )
        
        await message.reply(about_text)
    
    @router.message(Command('status'))
    async def status_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
            
        status_text = await generate_harsh_status_text(message.from_user, modules)
        await message.reply(status_text)
    
    # =================== AI КОМАНДЫ ===================
    
    @router.message(Command('ai'))
    async def ai_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
            
        if not modules.get('ai'):
            await message.reply("AI отключен.")
            return
        
        user_message = message.text[4:].strip()
        if not user_message:
            await message.reply(
                "<b>AI:</b>\n\n"
                "/ai [вопрос]\n\n"
                "<b>Примеры:</b>\n"
                "/ai Что такое Python\n"
                "/ai Объясни блокчейн"
            )
            return
        
        await process_harsh_ai_request(message, user_message, modules)
    
    @router.message(Command('memory_clear'))
    async def memory_clear_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if not modules.get('memory'):
            await message.reply("Память недоступна.")
            return
        
        success = await modules['memory'].clear_user_memory(
            message.from_user.id, message.chat.id
        )
        
        await message.reply("Память очищена." if success else "Ошибка очистки.")
    
    # =================== КРИПТОВАЛЮТЫ ===================
    
    @router.message(Command('crypto'))
    async def crypto_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
            
        if not modules.get('crypto'):
            await message.reply("Крипто отключено.")
            return
        
        coin_query = message.text[8:].strip()
        if not coin_query:
            await message.reply(
                "<b>Криптовалюты:</b>\n\n"
                "/crypto [монета]\n\n"
                "<b>Примеры:</b>\n"
                "/crypto bitcoin\n"
                "/crypto BTC"
            )
            return
        
        await process_crypto_request(message, coin_query, modules)
    
    # =================== АНАЛИТИКА ===================
    
    @router.message(Command('stats'))
    async def stats_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
            
        await process_user_stats(message, modules)
    
    # =================== АДМИНСКИЕ КОМАНДЫ (ТОЛЬКО ЛС) ===================
    
    @router.message(Command('moderation'))
    async def moderation_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        if message.chat.type != 'private':
            await message.reply("Модерация настраивается в ЛС.")
            return
            
        await process_moderation_settings(message, modules)
    
    @router.message(Command('triggers'))
    async def triggers_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
            
        await process_triggers_command(message, modules)
    
    @router.message(Command('trigger_add'))
    async def trigger_add_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
            
        await process_trigger_add(message, modules)
    
    @router.message(Command('trigger_del'))
    async def trigger_del_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
            
        await process_trigger_delete(message, modules)
    
    @router.message(Command('trigger_list'))
    async def trigger_list_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
            
        await process_trigger_list(message, modules)
    
    @router.message(Command('permissions'))
    async def permissions_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        if message.chat.type != 'private':
            await message.reply("Настройки доступа в ЛС.")
            return
            
        await process_permissions_command(message, modules)
    
    @router.message(Command('dashboard'))
    async def dashboard_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
            
        await process_user_dashboard(message, modules)
    
    @router.message(Command('export'))
    async def export_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
            
        await process_data_export(message, modules)
    
    # КОМАНДЫ МОДЕРАЦИИ В ГРУППАХ (ТОЛЬКО АДМИНЫ)
    @router.message(Command('ban'))
    async def ban_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        if message.chat.type == 'private':
            await message.reply("Только в группах.")
            return
            
        await process_ban_command(message, modules)
    
    @router.message(Command('mute'))
    async def mute_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        if message.chat.type == 'private':
            await message.reply("Только в группах.")
            return
            
        await process_mute_command(message, modules)
    
    @router.message(Command('warn'))
    async def warn_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        if message.chat.type == 'private':
            await message.reply("Только в группах.")
            return
            
        await process_warn_command(message, modules)
    
    # =================== ОБРАБОТКА СТИКЕРОВ ===================
    
    @router.message(F.sticker)
    async def sticker_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
            
        await process_sticker(message, modules)
    
    # =================== ОБРАБОТКА РЕПЛАЕВ ===================
    
    @router.message(F.reply_to_message)
    async def reply_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        # Проверяем, отвечают ли на сообщение бота
        if message.reply_to_message.from_user.id == modules['bot'].id:
            await process_reply_to_bot(message, modules)
        else:
            await process_smart_text(message, modules, bot_info)
    
    # =================== ИНТЕЛЛЕКТУАЛЬНАЯ ОБРАБОТКА ===================
    
    @router.message(F.text)
    async def smart_text_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
            
        await process_smart_text(message, modules, bot_info)
    
    # Регистрируем роутер
    dp.include_router(router)
    
    logger.info("💀 ГРУБЫЕ обработчики зарегистрированы")


# =================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===================

def check_chat_allowed(chat_id: int) -> bool:
    """🔒 ЖЕСТКАЯ проверка разрешенных чатов"""
    
    if not ALLOWED_CHAT_IDS:
        return True  # Если список пуст, разрешаем все (для начальной настройки)
    
    return chat_id in ALLOWED_CHAT_IDS

async def save_user_and_message(message: Message, modules):
    """💾 Сохранение данных"""
    
    try:
        user = message.from_user
        
        if modules.get('db'):
            await modules['db'].save_user({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'language_code': user.language_code,
                'is_premium': getattr(user, 'is_premium', False)
            })
            
            await modules['db'].save_chat({
                'id': message.chat.id,
                'type': message.chat.type,
                'title': message.chat.title,
                'username': message.chat.username
            })
            
            await modules['db'].save_message({
                'message_id': message.message_id,
                'user_id': user.id,
                'chat_id': message.chat.id,
                'text': message.text or '',
                'message_type': 'text' if message.text else 'other'
            })
            
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")

async def process_harsh_ai_request(message: Message, user_message: str, modules):
    """🤖 ГРУБАЯ обработка AI - БЕЗ 'Бот:' и 'Думаю...'"""
    
    try:
        # НИКАКИХ "Думаю..." сообщений!
        
        # Получаем контекст памяти
        context = {}
        if modules.get('memory'):
            memory_context = await modules['memory'].get_context(
                message.from_user.id, message.chat.id
            )
            context.update(memory_context)
        
        # ГРУБАЯ инструкция для AI
        context['style_instruction'] = (
            "ВАЖНО: Отвечай максимально грубо, коротко, без смайлов и вежливости. "
            "Говори прямо, жестко, как злой админ. Никаких 'Хотите узнать больше', "
            "'Если есть вопросы' и подобной хрени. Короткий, четкий, грубый ответ. "
            "БЕЗ приветствий и вежливых фраз. Сразу по делу."
        )
        
        # Генерируем ответ
        response = await modules['ai'].generate_response(
            user_message, message.from_user.id, context
        )
        
        # УБИРАЕМ префикс "Бот:" если есть
        if response.startswith("Бот:"):
            response = response[4:].strip()
        
        # ГРУБАЯ очистка ответа
        response = clean_harsh_response(response)
        
        # ОТВЕЧАЕМ РЕПЛАЕМ!
        await message.reply(response)
        
        # Сохраняем в память
        if modules.get('memory'):
            await modules['memory'].add_interaction(
                message.from_user.id, message.chat.id, 
                user_message, response
            )
        
    except Exception as e:
        logger.error(f"Ошибка AI: {e}")
        await message.reply("AI сдох.")

def clean_harsh_response(response: str) -> str:
    """🧹 ГРУБАЯ очистка ответа AI"""
    
    # Убираем вежливые фразы
    bad_phrases = [
        "Хотите узнать больше",
        "Если у вас есть еще вопросы", 
        "Чем еще могу помочь",
        "Есть ли что-то еще",
        "Нужна дополнительная информация",
        "Обращайтесь если нужно",
        "Рад был помочь",
        "Удачи вам",
        "Всего наилучшего",
        "С уважением",
        "Пожалуйста",
        "Спасибо за вопрос",
        "Надеюсь, помог",
        "Буду рад помочь"
    ]
    
    cleaned = response
    for phrase in bad_phrases:
        if phrase in cleaned:
            parts = cleaned.split(phrase)
            cleaned = parts[0].rstrip()
    
    # Убираем лишние смайлы
    emoji_pattern = r'[😊😄😃😆😁🤗🎉✨💫⭐🌟💡🔥👍👌🎯📚🔍💭🤔😌😇🥰😍🤩]+$'
    cleaned = re.sub(emoji_pattern, '', cleaned).strip()
    
    # Убираем вежливые слова в начале
    polite_starts = ["Конечно", "Безусловно", "С удовольствием", "Разумеется"]
    for start in polite_starts:
        if cleaned.startswith(start):
            cleaned = cleaned[len(start):].lstrip(", ")
    
    return cleaned.strip()

async def process_smart_text(message: Message, modules, bot_info):
    """🧠 Интеллектуальная обработка"""
    
    try:
        user = message.from_user
        text = message.text.lower()
        
        await save_user_and_message(message, modules)
        
        # 1. Проверяем триггеры
        if modules.get('triggers'):
            trigger_response = await modules['triggers'].check_message_triggers(
                message.text, message.chat.id, user.id
            )
            if trigger_response:
                await message.reply(trigger_response)
                return
        
        # 2. Проверяем модерацию
        moderation_action = await check_moderation(message, modules)
        if moderation_action:
            return
        
        # 3. Проверяем упоминания бота
        should_respond = await check_bot_mentions(message, bot_info)
        
        if should_respond:
            await process_harsh_smart_response(message, modules)
        else:
            await process_random_responses(message, modules)
        
        # Трекинг
        if modules.get('analytics'):
            await modules['analytics'].track_user_action(
                user.id, message.chat.id, 'message_sent',
                {'text_length': len(message.text), 'has_mention': should_respond}
            )
        
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")

async def check_bot_mentions(message: Message, bot_info) -> bool:
    """🎯 Проверка упоминаний"""
    
    try:
        if message.chat.type == 'private':
            return True
        
        text = message.text.lower()
        
        # Прямое упоминание
        if bot_info and f'@{bot_info.username.lower()}' in text:
            return True
        
        # Упоминание по имени
        if bot_info and bot_info.first_name.lower() in text:
            return True
        
        # Ключевые слова
        bot_keywords = ['бот', 'bot', 'робот', 'помощник']
        if any(keyword in text for keyword in bot_keywords):
            return True
        
        # Вопросы
        if '?' in message.text and len(message.text) > 15:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Ошибка проверки упоминаний: {e}")
        return False

async def process_harsh_smart_response(message: Message, modules):
    """💡 ГРУБЫЙ умный ответ"""
    
    try:
        if modules.get('ai'):
            await process_harsh_ai_request(message, message.text, modules)
        else:
            # Грубые базовые ответы
            harsh_responses = [
                "Что?",
                "AI отключен.",
                "Настрой API ключи.",
                "Не работает.",
                "Сломано."
            ]
            
            await message.reply(random.choice(harsh_responses))
        
    except Exception as e:
        logger.error(f"Ошибка умного ответа: {e}")

async def process_reply_to_bot(message: Message, modules):
    """💬 Обработка ответа на бота"""
    
    try:
        if modules.get('ai'):
            context_message = f"На мое сообщение '{message.reply_to_message.text}' пользователь ответил: '{message.text}'"
            await process_harsh_ai_request(message, context_message, modules)
        else:
            await message.reply("Понял.")
        
    except Exception as e:
        logger.error(f"Ошибка реплая: {e}")

async def check_moderation(message: Message, modules) -> bool:
    """🛡️ Модерация"""
    
    try:
        if not modules.get('moderation'):
            return False
            
        moderation_result = await modules['moderation'].check_message(
            message.from_user.id, message.chat.id, message.text
        )
        
        if moderation_result['action'] != 'allow':
            action = moderation_result['action']
            reason = moderation_result['reason']
            
            if action == 'delete':
                try:
                    await message.delete()
                    await message.reply(f"Удалено: {reason}")
                except:
                    await message.reply(f"Нарушение: {reason}")
            elif action == 'warn':
                warnings = moderation_result.get('user_warnings', 0)
                await message.reply(f"Предупреждение {warnings}: {reason}")
            elif action == 'timeout':
                await message.reply(f"Ограничение: {reason}")
            
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Ошибка модерации: {e}")
        return False

async def process_random_responses(message: Message, modules):
    """🎲 Случайные ответы"""
    
    try:
        if (modules.get('config') and 
            random.random() < 0.005):  # Очень редко
            
            harsh_responses = [
                "Ага.",
                "Понятно.",
                "Ясно.",
                "Окей."
            ]
            
            await message.reply(random.choice(harsh_responses))
            
    except Exception as e:
        logger.error(f"Ошибка случайных ответов: {e}")

async def generate_harsh_status_text(user, modules) -> str:
    """📊 ГРУБЫЙ статус системы"""
    
    status_parts = ["<b>БОТ v3.0 - СТАТУС</b>\n"]
    
    modules_status = []
    
    if modules.get('ai'):
        try:
            ai_stats = modules['ai'].get_usage_stats()
            modules_status.append(f"AI: Работает ({ai_stats.get('daily_usage', 0)} запросов)")
        except:
            modules_status.append("AI: Есть косяки")
    else:
        modules_status.append("AI: Отключен")
    
    if modules.get('crypto'):
        modules_status.append("Crypto: Работает")
    else:
        modules_status.append("Crypto: Отключен")
    
    if modules.get('triggers'):
        try:
            trigger_stats = await modules['triggers'].get_trigger_statistics()
            total = trigger_stats.get('total_triggers', 0)
            modules_status.append(f"Triggers: {total} штук")
        except:
            modules_status.append("Triggers: Работает")
    else:
        modules_status.append("Triggers: Отключен")
    
    other = ['analytics', 'memory', 'permissions', 'moderation']
    for module in other:
        status = "Работает" if modules.get(module) else "Отключен"
        modules_status.append(f"{module.title()}: {status}")
    
    status_parts.append("\n".join(modules_status))
    
    status_parts.append(f"\n<b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    status_parts.append(f"<b>ID:</b> {user.id}")
    status_parts.append(f"<b>Роль:</b> {'Админ' if user.id in modules['config'].bot.admin_ids else 'Юзер'}")
    status_parts.append(f"<b>Разрешенных чатов:</b> {len(ALLOWED_CHAT_IDS)}")
    
    return "\n\n".join(status_parts)

# =================== ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ ФУНКЦИЙ ===================

async def process_crypto_request(message, coin_query, modules): 
    await message.reply("Крипто в разработке.")

async def process_user_stats(message, modules): 
    await message.reply("Статистика в разработке.")

async def process_user_dashboard(message, modules): 
    await message.reply("Дашборд в разработке.")

async def process_data_export(message, modules): 
    await message.reply("Экспорт в разработке.")

async def process_sticker(message, modules): 
    await message.reply("Стикеры в разработке.")

async def process_triggers_command(message, modules): 
    await message.reply("Триггеры в разработке.")

async def process_trigger_add(message, modules): 
    await message.reply("Создание триггеров в разработке.")

async def process_trigger_delete(message, modules): 
    await message.reply("Удаление триггеров в разработке.")

async def process_trigger_list(message, modules): 
    await message.reply("Список триггеров в разработке.")

async def process_moderation_settings(message, modules): 
    await message.reply("Настройки модерации в разработке.")

async def process_ban_command(message, modules): 
    await message.reply("Бан в разработке.")

async def process_mute_command(message, modules): 
    await message.reply("Мут в разработке.")

async def process_warn_command(message, modules): 
    await message.reply("Варн в разработке.")

async def process_permissions_command(message, modules): 
    await message.reply("Разрешения в разработке.")


__all__ = ["register_all_handlers"]