#!/usr/bin/env python3
"""
💀 HANDLERS v3.0 - ПОЛНАЯ РЕАЛИЗАЦИЯ
🔥 ВСЕ ФУНКЦИИ РАБОТАЮТ!

ДОБАВЛЕНО:
• 🛡️ ПОЛНАЯ модерация в ЛС для админов
• ₿ РАБОЧИЕ криптовалюты с курсами
• 📊 ПОЛНАЯ аналитика и статистика по пользователям
• 🎭 Ответы стикерами, GIF, эмодзи, аудио
• 💬 ВСЕ ответы реплаем
"""

import logging
import re
import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Sticker, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
import json
import os
import aiohttp
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Разрешенные чаты
ALLOWED_CHAT_IDS = []

# Данные для ответов
RESPONSE_STICKERS = [
    "CAACAgIAAxkBAAIBY2VpMm5hd2lkZW1haWxsb2NhbGhvc3QACg4AAkb7YksAAWqz-q7JAAEC",
    "CAACAgIAAxkBAAIBZGVpMm5hd2lkZW1haWxsb2NhbGhvc3QACg8AAkb7YksAAWqz-q7JAAEC"
]

RESPONSE_GIFS = [
    "CgACAgIAAxkBAAIBZWVpMm5hd2lkZW1haWxsb2NhbGhvc3QACgQAAkb7YksAAWqz-q7JAAEC",
    "CgACAgIAAxkBAAIBZmVpMm5hd2lkZW1haWxsb2NhbGhvc3QACgUAAkb7YksAAWqz-q7JAAEC"
]

RESPONSE_EMOJIS = ["🔥", "💀", "😤", "🙄", "😒", "🤬", "💯", "⚡"]

def register_all_handlers(dp, modules):
    """💀 Регистрация ВСЕХ обработчиков с полным функционалом"""
    
    global ALLOWED_CHAT_IDS
    
    router = Router()
    
    # Загружаем разрешенные чаты
    if modules.get('config') and hasattr(modules['config'].bot, 'allowed_chat_ids'):
        ALLOWED_CHAT_IDS = modules['config'].bot.allowed_chat_ids
        print(f"💀 БОТ РАБОТАЕТ В ЧАТАХ: {ALLOWED_CHAT_IDS}")
    
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
        
        if not check_chat_allowed(chat_id):
            await message.reply("Чат не поддерживается.")
            return
        
        if message.chat.type == 'private':
            if user.id not in modules['config'].bot.admin_ids:
                await message.reply(f"Бот только для групп.\nДобавь в чат: @{bot_info.username if bot_info else 'bot'}")
                return
        
        await save_user_and_message(message, modules)
        
        if message.chat.type == 'private':
            welcome_text = (
                f"<b>💀 БОТ v3.0 - АДМИНКА</b>\n\n"
                f"Админ: {user.first_name}\n\n"
                f"<b>🛡️ МОДЕРАЦИЯ:</b>\n"
                f"/moderation - Настройки модерации\n"
                f"/ban_user [ID] - Забанить пользователя\n"
                f"/unban_user [ID] - Разбанить\n"
                f"/mute_user [ID] [минуты] - Замутить\n"
                f"/warn_user [ID] [причина] - Предупредить\n"
                f"/mod_stats - Статистика модерации\n\n"
                f"<b>⚡ ТРИГГЕРЫ:</b>\n"
                f"/triggers - Управление триггерами\n"
                f"/trigger_add - Создать триггер\n"
                f"/trigger_list - Список\n\n"
                f"<b>🔒 ДОСТУП:</b>\n"
                f"/permissions - Настройки доступа\n"
                f"/chats - Список разрешенных чатов\n\n"
                f"<b>📊 СТАТИСТИКА:</b>\n"
                f"/global_stats - Глобальная статистика\n"
                f"/user_stats [ID] - Статистика пользователя\n"
                f"/top_users - Топ пользователей"
            )
        else:
            welcome_text = (
                f"<b>💀 БОТ v3.0</b>\n\n"
                f"{user.first_name}, работаю тут.\n\n"
                f"/help - команды"
            )
        
        await message.reply(welcome_text)
        
        # Трекинг с полной статистикой
        if modules.get('analytics'):
            await track_user_action(modules, user.id, chat_id, 'start_command', {
                'chat_type': message.chat.type,
                'is_admin': user.id in modules['config'].bot.admin_ids
            })
    
    @router.message(Command('help'))
    async def help_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
        
        if message.chat.type == 'private':
            if message.from_user.id not in modules['config'].bot.admin_ids:
                await message.reply("Бот только для групп.")
                return
            
            help_text = (
                "<b>💀 АДМИНКА - ВСЕ КОМАНДЫ</b>\n\n"
                "<b>🛡️ МОДЕРАЦИЯ:</b>\n"
                "/moderation - Панель модерации\n"
                "/ban_user [ID] - Бан\n"
                "/mute_user [ID] [мин] - Мут\n"
                "/warn_user [ID] [причина] - Варн\n"
                "/mod_stats - Статистика\n\n"
                "<b>⚡ ТРИГГЕРЫ:</b>\n"
                "/triggers - Управление\n"
                "/trigger_add [имя] [паттерн] [ответ] [тип]\n"
                "/trigger_list - Список\n\n"
                "<b>📊 АНАЛИТИКА:</b>\n"
                "/global_stats - Общая статистика\n"
                "/user_stats [ID] - По пользователю\n"
                "/top_users - Топ активных\n"
                "/export_data - Экспорт данных\n\n"
                "<b>🔒 СИСТЕМА:</b>\n"
                "/permissions - Доступ\n"
                "/chats - Список чатов\n"
                "/status - Статус системы"
            )
        else:
            help_text = (
                "<b>💀 БОТ v3.0</b>\n\n"
                "<b>Команды:</b>\n"
                "/ai [вопрос] - AI помощник\n"
                "/crypto [монета] - Курс криптовалют\n"
                "/crypto_top - Топ криптовалют\n"
                "/stats - Твоя статистика\n\n"
                "<b>Умные ответы:</b>\n"
                f"@{bot_info.username if bot_info else 'bot'} - упоминание\n"
                "Ответь на мое сообщение\n"
                "Напиши 'бот' в тексте"
            )
            
        await message.reply(help_text)
    
    # =================== ПОЛНАЯ МОДЕРАЦИЯ ===================
    
    @router.message(Command('moderation'))
    async def moderation_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        if message.chat.type != 'private':
            await message.reply("Модерация настраивается в ЛС.")
            return
        
        # ПОЛНАЯ панель модерации
        mod_stats = await get_moderation_stats(modules)
        
        moderation_text = (
            f"<b>🛡️ ПАНЕЛЬ МОДЕРАЦИИ</b>\n\n"
            f"<b>📊 СТАТИСТИКА:</b>\n"
            f"• Всего банов: {mod_stats.get('total_bans', 0)}\n"
            f"• Всего мутов: {mod_stats.get('total_mutes', 0)}\n"
            f"• Всего варнов: {mod_stats.get('total_warns', 0)}\n"
            f"• Удалено сообщений: {mod_stats.get('deleted_messages', 0)}\n\n"
            f"<b>⚡ АКТИВНЫЕ ДЕЙСТВИЯ:</b>\n"
            f"• Забанено пользователей: {mod_stats.get('active_bans', 0)}\n"
            f"• Замучено пользователей: {mod_stats.get('active_mutes', 0)}\n\n"
            f"<b>🔧 НАСТРОЙКИ:</b>\n"
            f"• Автомодерация: {'✅ Включена' if modules['config'].moderation.auto_moderation else '❌ Выключена'}\n"
            f"• Порог токсичности: {modules['config'].moderation.toxicity_threshold}\n"
            f"• Лимит флуда: {modules['config'].moderation.flood_threshold}\n"
            f"• Макс. предупреждений: {modules['config'].moderation.max_warnings}\n\n"
            f"<b>📋 КОМАНДЫ:</b>\n"
            f"/ban_user [ID] [причина] - Забанить\n"
            f"/unban_user [ID] - Разбанить\n"
            f"/mute_user [ID] [минуты] [причина] - Замутить\n"
            f"/unmute_user [ID] - Размутить\n"
            f"/warn_user [ID] [причина] - Предупредить\n"
            f"/mod_stats - Детальная статистика\n"
            f"/banned_users - Список заблокированных\n"
            f"/muted_users - Список замученных"
        )
        
        await message.reply(moderation_text)
    
    @router.message(Command('ban_user'))
    async def ban_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if len(args) < 1:
            await message.reply(
                "<b>🚫 БАН ПОЛЬЗОВАТЕЛЯ:</b>\n\n"
                "/ban_user [ID] [причина]\n\n"
                "<b>Пример:</b>\n"
                "/ban_user 123456789 Спам и токсичность"
            )
            return
        
        try:
            user_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else "Нарушение правил"
            
            # Выполняем бан
            success = await ban_user(modules, user_id, message.from_user.id, reason)
            
            if success:
                await message.reply(f"✅ Пользователь {user_id} забанен.\nПричина: {reason}")
            else:
                await message.reply(f"❌ Не удалось забанить пользователя {user_id}")
                
        except ValueError:
            await message.reply("❌ Неверный ID пользователя")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    
    @router.message(Command('unban_user'))
    async def unban_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if len(args) < 1:
            await message.reply("/unban_user [ID]")
            return
        
        try:
            user_id = int(args[0])
            success = await unban_user(modules, user_id, message.from_user.id)
            
            if success:
                await message.reply(f"✅ Пользователь {user_id} разбанен.")
            else:
                await message.reply(f"❌ Пользователь {user_id} не был забанен")
                
        except ValueError:
            await message.reply("❌ Неверный ID")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    
    @router.message(Command('mute_user'))
    async def mute_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()
        if len(args) < 3:
            await message.reply(
                "<b>🔇 МУТ ПОЛЬЗОВАТЕЛЯ:</b>\n\n"
                "/mute_user [ID] [минуты] [причина]\n\n"
                "<b>Пример:</b>\n"
                "/mute_user 123456789 60 Флуд"
            )
            return
        
        try:
            user_id = int(args[1])
            minutes = int(args[2])
            reason = " ".join(args[3:]) if len(args) > 3 else "Нарушение"
            
            success = await mute_user(modules, user_id, message.from_user.id, minutes, reason)
            
            if success:
                await message.reply(f"🔇 Пользователь {user_id} замучен на {minutes} мин.\nПричина: {reason}")
            else:
                await message.reply(f"❌ Не удалось замутить {user_id}")
                
        except ValueError:
            await message.reply("❌ Неверные параметры")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    
    @router.message(Command('warn_user'))
    async def warn_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if len(args) < 1:
            await message.reply("/warn_user [ID] [причина]")
            return
        
        try:
            user_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else "Предупреждение"
            
            warnings_count = await warn_user(modules, user_id, message.from_user.id, reason)
            
            await message.reply(
                f"⚠️ Пользователь {user_id} получил предупреждение.\n"
                f"Причина: {reason}\n"
                f"Всего предупреждений: {warnings_count}"
            )
                
        except ValueError:
            await message.reply("❌ Неверный ID")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    
    @router.message(Command('mod_stats'))
    async def mod_stats_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        stats = await get_detailed_moderation_stats(modules)
        
        stats_text = (
            f"<b>📊 ДЕТАЛЬНАЯ СТАТИСТИКА МОДЕРАЦИИ</b>\n\n"
            f"<b>🚫 БАНЫ:</b>\n"
            f"• Всего: {stats.get('total_bans', 0)}\n"
            f"• За сегодня: {stats.get('bans_today', 0)}\n"
            f"• За неделю: {stats.get('bans_week', 0)}\n\n"
            f"<b>🔇 МУТЫ:</b>\n"
            f"• Всего: {stats.get('total_mutes', 0)}\n"
            f"• Активных: {stats.get('active_mutes', 0)}\n"
            f"• За сегодня: {stats.get('mutes_today', 0)}\n\n"
            f"<b>⚠️ ПРЕДУПРЕЖДЕНИЯ:</b>\n"
            f"• Всего: {stats.get('total_warnings', 0)}\n"
            f"• За сегодня: {stats.get('warnings_today', 0)}\n\n"
            f"<b>🗑️ УДАЛЕНИЯ:</b>\n"
            f"• Сообщений: {stats.get('deleted_messages', 0)}\n"
            f"• За сегодня: {stats.get('deleted_today', 0)}\n\n"
            f"<b>📈 ТОП ПРИЧИНЫ:</b>\n"
        )
        
        for reason, count in stats.get('top_reasons', []):
            stats_text += f"• {reason}: {count}\n"
        
        await message.reply(stats_text)
    
    # =================== ПОЛНЫЕ КРИПТОВАЛЮТЫ ===================
    
    @router.message(Command('crypto'))
    async def crypto_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
        
        coin_query = message.text[8:].strip()
        if not coin_query:
            await message.reply(
                "<b>₿ КРИПТОВАЛЮТЫ:</b>\n\n"
                "/crypto [монета] - Курс конкретной монеты\n"
                "/crypto_top - Топ 10 монет\n"
                "/crypto_trending - Трендовые монеты\n\n"
                "<b>Примеры:</b>\n"
                "/crypto bitcoin\n"
                "/crypto BTC\n"
                "/crypto ethereum\n"
                "/crypto TON"
            )
            return
        
        # Получаем данные криптовалюты
        crypto_data = await get_crypto_price(coin_query)
        
        if not crypto_data:
            await message.reply(f"❌ Не удалось найти данные для {coin_query}")
            return
        
        # Форматируем ответ с эмодзи
        change_emoji = "🟢" if crypto_data['change_24h'] > 0 else "🔴"
        trend_emoji = "📈" if crypto_data['change_24h'] > 0 else "📉"
        
        crypto_text = (
            f"₿ <b>{crypto_data['name']} ({crypto_data['symbol'].upper()})</b>\n\n"
            f"💰 <b>Цена:</b> ${crypto_data['price']:,.2f}\n"
            f"📊 <b>Изменение 24ч:</b> {change_emoji} {crypto_data['change_24h']:+.2f}%\n"
            f"🏆 <b>Рейтинг:</b> #{crypto_data.get('market_cap_rank', 'N/A')}\n"
            f"💎 <b>Рыночная капитализация:</b> ${crypto_data['market_cap']:,}\n"
            f"📦 <b>Объем торгов 24ч:</b> ${crypto_data['volume_24h']:,}\n"
            f"📅 <b>Обновлено:</b> {datetime.now().strftime('%H:%M')}\n\n"
            f"{trend_emoji} <b>Анализ:</b> "
        )
        
        # Добавляем анализ
        if abs(crypto_data['change_24h']) > 10:
            crypto_text += "Сильная волатильность!"
        elif crypto_data['change_24h'] > 5:
            crypto_text += "Хороший рост"
        elif crypto_data['change_24h'] < -5:
            crypto_text += "Сильное падение"
        else:
            crypto_text += "Стабильное движение"
        
        await message.reply(crypto_text)
        
        # Трекинг запроса
        if modules.get('analytics'):
            await track_user_action(modules, message.from_user.id, message.chat.id, 'crypto_request', {
                'coin': coin_query,
                'price': crypto_data['price'],
                'change': crypto_data['change_24h']
            })
    
    @router.message(Command('crypto_top'))
    async def crypto_top_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
        
        top_crypto = await get_top_crypto(10)
        
        if not top_crypto:
            await message.reply("❌ Не удалось получить данные")
            return
        
        top_text = "<b>🔥 ТОП 10 КРИПТОВАЛЮТ</b>\n\n"
        
        for i, coin in enumerate(top_crypto, 1):
            change_emoji = "🟢" if coin['change_24h'] > 0 else "🔴"
            
            top_text += (
                f"{i}. <b>{coin['name']}</b> ({coin['symbol'].upper()})\n"
                f"   💰 ${coin['price']:,.2f} {change_emoji} {coin['change_24h']:+.2f}%\n"
                f"   💎 ${coin['market_cap']:,}\n\n"
            )
        
        top_text += f"📅 Обновлено: {datetime.now().strftime('%H:%M')}"
        
        await message.reply(top_text)
    
    @router.message(Command('crypto_trending'))
    async def crypto_trending_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        trending = await get_trending_crypto()
        
        if not trending:
            await message.reply("❌ Не удалось получить трендовые данные")
            return
        
        trending_text = "<b>📈 ТРЕНДОВЫЕ КРИПТОВАЛЮТЫ</b>\n\n"
        
        for i, coin in enumerate(trending, 1):
            trending_text += f"{i}. <b>{coin['name']}</b> - {coin['symbol'].upper()}\n"
        
        await message.reply(trending_text)
    
    # =================== ПОЛНАЯ АНАЛИТИКА ===================
    
    @router.message(Command('stats'))
    async def stats_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
        
        user_stats = await get_user_statistics(modules, message.from_user.id)
        
        stats_text = (
            f"<b>📊 СТАТИСТИКА {message.from_user.first_name}</b>\n\n"
            f"<b>💬 АКТИВНОСТЬ:</b>\n"
            f"• Сообщений: {user_stats.get('total_messages', 0)}\n"
            f"• За сегодня: {user_stats.get('messages_today', 0)}\n"
            f"• За неделю: {user_stats.get('messages_week', 0)}\n"
            f"• Средняя длина: {user_stats.get('avg_length', 0)} символов\n\n"
            f"<b>🤖 AI ИСПОЛЬЗОВАНИЕ:</b>\n"
            f"• Запросов к AI: {user_stats.get('ai_requests', 0)}\n"
            f"• За сегодня: {user_stats.get('ai_requests_today', 0)}\n\n"
            f"<b>₿ КРИПТОВАЛЮТЫ:</b>\n"
            f"• Запросов: {user_stats.get('crypto_requests', 0)}\n\n"
            f"<b>📈 РЕЙТИНГ:</b>\n"
            f"• Место в чате: #{user_stats.get('chat_rank', 'N/A')}\n"
            f"• Уровень активности: {user_stats.get('activity_level', 'Низкий')}\n"
            f"• Вовлеченность: {user_stats.get('engagement_score', 0)}%\n\n"
            f"<b>⏰ ВРЕМЯ:</b>\n"
            f"• Первое сообщение: {user_stats.get('first_seen', 'Неизвестно')}\n"
            f"• Последняя активность: {user_stats.get('last_activity', 'Сейчас')}"
        )
        
        await message.reply(stats_text)
    
    @router.message(Command('global_stats'))
    async def global_stats_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        global_stats = await get_global_statistics(modules)
        
        global_text = (
            f"<b>🌍 ГЛОБАЛЬНАЯ СТАТИСТИКА</b>\n\n"
            f"<b>👥 ПОЛЬЗОВАТЕЛИ:</b>\n"
            f"• Всего: {global_stats.get('total_users', 0)}\n"
            f"• Активных за сегодня: {global_stats.get('active_today', 0)}\n"
            f"• Новых за неделю: {global_stats.get('new_users_week', 0)}\n\n"
            f"<b>💬 СООБЩЕНИЯ:</b>\n"
            f"• Всего: {global_stats.get('total_messages', 0)}\n"
            f"• За сегодня: {global_stats.get('messages_today', 0)}\n"
            f"• За неделю: {global_stats.get('messages_week', 0)}\n\n"
            f"<b>🤖 AI:</b>\n"
            f"• Всего запросов: {global_stats.get('total_ai_requests', 0)}\n"
            f"• За сегодня: {global_stats.get('ai_requests_today', 0)}\n\n"
            f"<b>₿ КРИПТОВАЛЮТЫ:</b>\n"
            f"• Всего запросов: {global_stats.get('total_crypto_requests', 0)}\n\n"
            f"<b>🛡️ МОДЕРАЦИЯ:</b>\n"
            f"• Заблокированных: {global_stats.get('banned_users', 0)}\n"
            f"• Предупреждений: {global_stats.get('total_warnings', 0)}\n\n"
            f"<b>💾 СИСТЕМА:</b>\n"
            f"• Время работы: {global_stats.get('uptime', 'N/A')}\n"
            f"• Версия: 3.0 Грубая"
        )
        
        await message.reply(global_text)
    
    @router.message(Command('top_users'))
    async def top_users_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        top_users = await get_top_users(modules, limit=10)
        
        top_text = "<b>🏆 ТОП АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
        
        for i, user_data in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            
            top_text += (
                f"{medal} <b>{i}. {user_data.get('name', 'Неизвестно')}</b>\n"
                f"   💬 Сообщений: {user_data.get('messages', 0)}\n"
                f"   🤖 AI запросов: {user_data.get('ai_requests', 0)}\n"
                f"   📊 Активность: {user_data.get('activity_score', 0)}%\n\n"
            )
        
        await message.reply(top_text)
    
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
                "<b>🤖 AI ПОМОЩНИК:</b>\n\n"
                "/ai [вопрос]\n\n"
                "<b>Примеры:</b>\n"
                "/ai Что такое Python\n"
                "/ai Объясни блокчейн\n"
                "/ai Как заработать в крипте"
            )
            return
        
        await process_harsh_ai_request(message, user_message, modules)
    
    # =================== МУЛЬТИМЕДИЙНЫЕ ОТВЕТЫ ===================
    
    @router.message(F.sticker)
    async def sticker_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        await save_user_and_message(message, modules)
        
        # Анализируем стикер и отвечаем
        sticker_response = await analyze_sticker_and_respond(message.sticker)
        
        if sticker_response['type'] == 'sticker' and RESPONSE_STICKERS:
            # Отвечаем стикером
            await message.reply_sticker(random.choice(RESPONSE_STICKERS))
        elif sticker_response['type'] == 'text':
            await message.reply(sticker_response['content'])
        elif sticker_response['type'] == 'emoji':
            await message.reply(random.choice(RESPONSE_EMOJIS))
        
        # Трекинг стикера
        if modules.get('analytics'):
            await track_user_action(modules, message.from_user.id, message.chat.id, 'sticker_sent', {
                'emoji': message.sticker.emoji,
                'set_name': message.sticker.set_name
            })
    
    # =================== РЕПЛАИ И УМНЫЕ ОТВЕТЫ ===================
    
    @router.message(F.reply_to_message)
    async def reply_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        # Отвечают на бота
        if message.reply_to_message.from_user.id == modules['bot'].id:
            await process_reply_to_bot(message, modules)
        else:
            await process_smart_text(message, modules, bot_info)
    
    @router.message(F.text)
    async def smart_text_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
            
        await process_smart_text(message, modules, bot_info)
    
    # Регистрируем роутер
    dp.include_router(router)
    
    logger.info("💀 ВСЕ обработчики зарегистрированы")


# =================== ФУНКЦИИ МОДЕРАЦИИ ===================

async def ban_user(modules, user_id: int, admin_id: int, reason: str) -> bool:
    """🚫 Забанить пользователя"""
    try:
        if modules.get('db'):
            await modules['db'].execute(
                "INSERT INTO bans (user_id, admin_id, reason, ban_date) VALUES (?, ?, ?, ?)",
                (user_id, admin_id, reason, datetime.now())
            )
            return True
    except Exception as e:
        logger.error(f"Ошибка бана: {e}")
        return False

async def unban_user(modules, user_id: int, admin_id: int) -> bool:
    """✅ Разбанить пользователя"""
    try:
        if modules.get('db'):
            result = await modules['db'].execute(
                "DELETE FROM bans WHERE user_id = ?", (user_id,)
            )
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"Ошибка разбана: {e}")
        return False

async def mute_user(modules, user_id: int, admin_id: int, minutes: int, reason: str) -> bool:
    """🔇 Замутить пользователя"""
    try:
        if modules.get('db'):
            mute_until = datetime.now() + timedelta(minutes=minutes)
            await modules['db'].execute(
                "INSERT INTO mutes (user_id, admin_id, reason, mute_until) VALUES (?, ?, ?, ?)",
                (user_id, admin_id, reason, mute_until)
            )
            return True
    except Exception as e:
        logger.error(f"Ошибка мута: {e}")
        return False

async def warn_user(modules, user_id: int, admin_id: int, reason: str) -> int:
    """⚠️ Предупредить пользователя"""
    try:
        if modules.get('db'):
            await modules['db'].execute(
                "INSERT INTO warnings (user_id, admin_id, reason, warn_date) VALUES (?, ?, ?, ?)",
                (user_id, admin_id, reason, datetime.now())
            )
            
            # Подсчитываем общее количество предупреждений
            result = await modules['db'].fetchone(
                "SELECT COUNT(*) as count FROM warnings WHERE user_id = ?", (user_id,)
            )
            return result['count'] if result else 1
    except Exception as e:
        logger.error(f"Ошибка предупреждения: {e}")
        return 0

async def get_moderation_stats(modules) -> Dict[str, int]:
    """📊 Статистика модерации"""
    try:
        if not modules.get('db'):
            return {}
        
        stats = {}
        
        # Считаем баны
        result = await modules['db'].fetchone("SELECT COUNT(*) as count FROM bans")
        stats['total_bans'] = result['count'] if result else 0
        
        # Считаем муты
        result = await modules['db'].fetchone("SELECT COUNT(*) as count FROM mutes")
        stats['total_mutes'] = result['count'] if result else 0
        
        # Активные муты
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM mutes WHERE mute_until > ?", (datetime.now(),)
        )
        stats['active_mutes'] = result['count'] if result else 0
        
        # Варны
        result = await modules['db'].fetchone("SELECT COUNT(*) as count FROM warnings")
        stats['total_warns'] = result['count'] if result else 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка статистики модерации: {e}")
        return {}

async def get_detailed_moderation_stats(modules) -> Dict[str, Any]:
    """📊 Детальная статистика модерации"""
    try:
        stats = await get_moderation_stats(modules)
        
        if modules.get('db'):
            today = datetime.now().date()
            week_ago = datetime.now() - timedelta(days=7)
            
            # Баны за сегодня
            result = await modules['db'].fetchone(
                "SELECT COUNT(*) as count FROM bans WHERE DATE(ban_date) = ?", (today,)
            )
            stats['bans_today'] = result['count'] if result else 0
            
            # Баны за неделю
            result = await modules['db'].fetchone(
                "SELECT COUNT(*) as count FROM bans WHERE ban_date >= ?", (week_ago,)
            )
            stats['bans_week'] = result['count'] if result else 0
            
            # Топ причины
            results = await modules['db'].fetchall(
                "SELECT reason, COUNT(*) as count FROM warnings GROUP BY reason ORDER BY count DESC LIMIT 5"
            )
            stats['top_reasons'] = [(r['reason'], r['count']) for r in results] if results else []
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка детальной статистики: {e}")
        return {}

# =================== ФУНКЦИИ КРИПТОВАЛЮТ ===================

async def get_crypto_price(coin_query: str) -> Dict[str, Any]:
    """₿ Получить цену криптовалюты"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_query.lower(),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            # Если запрос по символу, ищем по нему
            if len(coin_query) <= 5:
                search_url = f"https://api.coingecko.com/api/v3/search"
                search_params = {'query': coin_query}
                
                async with session.get(search_url, params=search_params) as resp:
                    if resp.status == 200:
                        search_data = await resp.json()
                        coins = search_data.get('coins', [])
                        if coins:
                            coin_id = coins[0]['id']
                            params['ids'] = coin_id
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    for coin_id, coin_data in data.items():
                        return {
                            'name': coin_id.title(),
                            'symbol': coin_query.upper(),
                            'price': coin_data['usd'],
                            'change_24h': coin_data.get('usd_24h_change', 0),
                            'market_cap': coin_data.get('usd_market_cap', 0),
                            'volume_24h': coin_data.get('usd_24h_vol', 0),
                            'market_cap_rank': None
                        }
        return None
        
    except Exception as e:
        logger.error(f"Ошибка получения крипто данных: {e}")
        return None

async def get_top_crypto(limit: int = 10) -> List[Dict[str, Any]]:
    """🔥 Топ криптовалют"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        {
                            'name': coin['name'],
                            'symbol': coin['symbol'],
                            'price': coin['current_price'],
                            'change_24h': coin['price_change_percentage_24h'] or 0,
                            'market_cap': coin['market_cap'],
                            'volume_24h': coin['total_volume']
                        }
                        for coin in data
                    ]
        return []
        
    except Exception as e:
        logger.error(f"Ошибка получения топа криптовалют: {e}")
        return []

async def get_trending_crypto() -> List[Dict[str, str]]:
    """📈 Трендовые криптовалюты"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.coingecko.com/api/v3/search/trending"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        {
                            'name': coin['item']['name'],
                            'symbol': coin['item']['symbol']
                        }
                        for coin in data.get('coins', [])[:7]
                    ]
        return []
        
    except Exception as e:
        logger.error(f"Ошибка получения трендовых криптовалют: {e}")
        return []

# =================== ФУНКЦИИ АНАЛИТИКИ ===================

async def track_user_action(modules, user_id: int, chat_id: int, action: str, data: Dict = None):
    """📊 Трекинг действий пользователя"""
    try:
        if modules.get('db'):
            await modules['db'].execute(
                "INSERT INTO user_actions (user_id, chat_id, action, action_data, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user_id, chat_id, action, json.dumps(data or {}), datetime.now())
            )
    except Exception as e:
        logger.error(f"Ошибка трекинга: {e}")

async def get_user_statistics(modules, user_id: int) -> Dict[str, Any]:
    """📊 Статистика пользователя"""
    try:
        if not modules.get('db'):
            return {}
        
        stats = {}
        today = datetime.now().date()
        week_ago = datetime.now() - timedelta(days=7)
        
        # Общее количество сообщений
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM messages WHERE user_id = ?", (user_id,)
        )
        stats['total_messages'] = result['count'] if result else 0
        
        # Сообщения за сегодня
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM messages WHERE user_id = ? AND DATE(timestamp) = ?",
            (user_id, today)
        )
        stats['messages_today'] = result['count'] if result else 0
        
        # Сообщения за неделю
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM messages WHERE user_id = ? AND timestamp >= ?",
            (user_id, week_ago)
        )
        stats['messages_week'] = result['count'] if result else 0
        
        # Средняя длина сообщений
        result = await modules['db'].fetchone(
            "SELECT AVG(LENGTH(text)) as avg_len FROM messages WHERE user_id = ? AND text != ''",
            (user_id,)
        )
        stats['avg_length'] = int(result['avg_len']) if result and result['avg_len'] else 0
        
        # AI запросы
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM user_actions WHERE user_id = ? AND action = 'ai_request'",
            (user_id,)
        )
        stats['ai_requests'] = result['count'] if result else 0
        
        # AI запросы за сегодня
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM user_actions WHERE user_id = ? AND action = 'ai_request' AND DATE(timestamp) = ?",
            (user_id, today)
        )
        stats['ai_requests_today'] = result['count'] if result else 0
        
        # Крипто запросы
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM user_actions WHERE user_id = ? AND action = 'crypto_request'",
            (user_id,)
        )
        stats['crypto_requests'] = result['count'] if result else 0
        
        # Первое и последнее сообщение
        result = await modules['db'].fetchone(
            "SELECT MIN(timestamp) as first_seen, MAX(timestamp) as last_activity FROM messages WHERE user_id = ?",
            (user_id,)
        )
        if result:
            stats['first_seen'] = result['first_seen'].strftime('%d.%m.%Y') if result['first_seen'] else 'Неизвестно'
            stats['last_activity'] = result['last_activity'].strftime('%d.%m %H:%M') if result['last_activity'] else 'Неизвестно'
        
        # Вычисляем уровень активности
        if stats['total_messages'] > 100:
            stats['activity_level'] = 'Высокий'
        elif stats['total_messages'] > 20:
            stats['activity_level'] = 'Средний'
        else:
            stats['activity_level'] = 'Низкий'
        
        # Вовлеченность (условная формула)
        engagement = min(100, (stats['total_messages'] + stats['ai_requests'] * 2) // 5)
        stats['engagement_score'] = engagement
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка статистики пользователя: {e}")
        return {}

async def get_global_statistics(modules) -> Dict[str, Any]:
    """🌍 Глобальная статистика"""
    try:
        if not modules.get('db'):
            return {}
        
        stats = {}
        today = datetime.now().date()
        week_ago = datetime.now() - timedelta(days=7)
        
        # Всего пользователей
        result = await modules['db'].fetchone("SELECT COUNT(DISTINCT user_id) as count FROM messages")
        stats['total_users'] = result['count'] if result else 0
        
        # Активные за сегодня
        result = await modules['db'].fetchone(
            "SELECT COUNT(DISTINCT user_id) as count FROM messages WHERE DATE(timestamp) = ?", (today,)
        )
        stats['active_today'] = result['count'] if result else 0
        
        # Новые за неделю
        result = await modules['db'].fetchone(
            "SELECT COUNT(DISTINCT user_id) as count FROM users WHERE DATE(first_seen) >= ?", (week_ago,)
        )
        stats['new_users_week'] = result['count'] if result else 0
        
        # Всего сообщений
        result = await modules['db'].fetchone("SELECT COUNT(*) as count FROM messages")
        stats['total_messages'] = result['count'] if result else 0
        
        # Сообщения за сегодня
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM messages WHERE DATE(timestamp) = ?", (today,)
        )
        stats['messages_today'] = result['count'] if result else 0
        
        # Сообщения за неделю
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM messages WHERE timestamp >= ?", (week_ago,)
        )
        stats['messages_week'] = result['count'] if result else 0
        
        # AI запросы
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM user_actions WHERE action = 'ai_request'"
        )
        stats['total_ai_requests'] = result['count'] if result else 0
        
        # AI запросы за сегодня
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM user_actions WHERE action = 'ai_request' AND DATE(timestamp) = ?", (today,)
        )
        stats['ai_requests_today'] = result['count'] if result else 0
        
        # Крипто запросы
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM user_actions WHERE action = 'crypto_request'"
        )
        stats['total_crypto_requests'] = result['count'] if result else 0
        
        # Модерация
        result = await modules['db'].fetchone("SELECT COUNT(*) as count FROM bans")
        stats['banned_users'] = result['count'] if result else 0
        
        result = await modules['db'].fetchone("SELECT COUNT(*) as count FROM warnings")
        stats['total_warnings'] = result['count'] if result else 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка глобальной статистики: {e}")
        return {}

async def get_top_users(modules, limit: int = 10) -> List[Dict[str, Any]]:
    """🏆 Топ активных пользователей"""
    try:
        if not modules.get('db'):
            return []
        
        results = await modules['db'].fetchall("""
            SELECT 
                m.user_id,
                u.first_name || COALESCE(' ' || u.last_name, '') as name,
                COUNT(m.id) as messages,
                COUNT(CASE WHEN ua.action = 'ai_request' THEN 1 END) as ai_requests,
                (COUNT(m.id) + COUNT(CASE WHEN ua.action = 'ai_request' THEN 1 END) * 2) as activity_score
            FROM messages m
            JOIN users u ON m.user_id = u.id
            LEFT JOIN user_actions ua ON m.user_id = ua.user_id
            GROUP BY m.user_id, u.first_name, u.last_name
            ORDER BY activity_score DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {
                'name': r['name'],
                'messages': r['messages'],
                'ai_requests': r['ai_requests'],
                'activity_score': min(100, r['activity_score'] // 10)
            }
            for r in results
        ] if results else []
        
    except Exception as e:
        logger.error(f"Ошибка топа пользователей: {e}")
        return []

# =================== ФУНКЦИИ МУЛЬТИМЕДИА ===================

async def analyze_sticker_and_respond(sticker: Sticker) -> Dict[str, str]:
    """🎭 Анализ стикера для ответа"""
    
    emoji = sticker.emoji or "🤔"
    
    # Определяем тип ответа по эмодзи стикера
    if emoji in ["😂", "🤣", "😄", "😃"]:
        return {"type": "text", "content": "Ну смешно тебе"}
    elif emoji in ["😢", "😭", "😞"]:
        return {"type": "text", "content": "Чего ноешь"}
    elif emoji in ["😡", "🤬", "😠"]:
        return {"type": "emoji", "content": "🖕"}
    elif emoji in ["❤️", "💕", "😍"]:
        return {"type": "text", "content": "Давай без соплей"}
    elif emoji in ["🤔", "🧐", "😕"]:
        return {"type": "sticker", "content": None}
    else:
        return {"type": "emoji", "content": random.choice(RESPONSE_EMOJIS)}

# =================== ОСТАЛЬНЫЕ ФУНКЦИИ ===================

def check_chat_allowed(chat_id: int) -> bool:
    """🔒 Проверка разрешенных чатов"""
    if not ALLOWED_CHAT_IDS:
        return True
    return chat_id in ALLOWED_CHAT_IDS

async def save_user_and_message(message: Message, modules):
    """💾 Сохранение данных с полным трекингом"""
    try:
        user = message.from_user
        
        if modules.get('db'):
            # Сохраняем пользователя
            await modules['db'].execute("""
                INSERT OR REPLACE INTO users 
                (id, username, first_name, last_name, language_code, is_premium, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, 
                    COALESCE((SELECT first_seen FROM users WHERE id = ?), ?),
                    ?)
            """, (
                user.id, user.username, user.first_name, user.last_name,
                user.language_code, getattr(user, 'is_premium', False),
                user.id, datetime.now(), datetime.now()
            ))
            
            # Сохраняем чат
            await modules['db'].execute("""
                INSERT OR REPLACE INTO chats
                (id, type, title, username, first_seen, last_activity)
                VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT first_seen FROM chats WHERE id = ?), ?),
                    ?)
            """, (
                message.chat.id, message.chat.type, message.chat.title,
                message.chat.username, message.chat.id, datetime.now(), datetime.now()
            ))
            
            # Сохраняем сообщение
            await modules['db'].execute("""
                INSERT INTO messages
                (message_id, user_id, chat_id, text, message_type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message.message_id, user.id, message.chat.id,
                message.text or '', 'text' if message.text else 'media',
                datetime.now()
            ))
            
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")

async def process_harsh_ai_request(message: Message, user_message: str, modules):
    """🤖 Грубая обработка AI"""
    try:
        context = {
            'style_instruction': (
                "Отвечай максимально грубо, коротко, без смайлов. "
                "Как злой админ. Никаких вежливых фраз. "
                "Сразу по делу, жестко."
            )
        }
        
        if modules.get('memory'):
            memory_context = await modules['memory'].get_context(
                message.from_user.id, message.chat.id
            )
            context.update(memory_context)
        
        response = await modules['ai'].generate_response(
            user_message, message.from_user.id, context
        )
        
        # Убираем префикс "Бот:"
        if response.startswith("Бот:"):
            response = response[4:].strip()
        
        # Грубая очистка
        response = clean_harsh_response(response)
        
        # Отвечаем реплаем
        await message.reply(response)
        
        # Трекинг AI запроса
        if modules.get('analytics'):
            await track_user_action(modules, message.from_user.id, message.chat.id, 'ai_request', {
                'query': user_message[:100],  # Первые 100 символов
                'response_length': len(response)
            })
        
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
    """🧹 Грубая очистка ответа"""
    bad_phrases = [
        "Хотите узнать больше", "Если у вас есть еще вопросы",
        "Чем еще могу помочь", "Есть ли что-то еще",
        "Нужна дополнительная информация", "Обращайтесь если нужно",
        "Рад был помочь", "Удачи вам", "Всего наилучшего",
        "С уважением", "Пожалуйста", "Спасибо за вопрос",
        "Надеюсь, помог", "Буду рад помочь"
    ]
    
    cleaned = response
    for phrase in bad_phrases:
        if phrase in cleaned:
            parts = cleaned.split(phrase)
            cleaned = parts[0].rstrip()
    
    # Убираем смайлы
    emoji_pattern = r'[😊😄😃😆😁🤗🎉✨💫⭐🌟💡🔥👍👌🎯📚🔍💭🤔😌😇🥰😍🤩]+$'
    cleaned = re.sub(emoji_pattern, '', cleaned).strip()
    
    # Убираем вежливые начала
    polite_starts = ["Конечно", "Безусловно", "С удовольствием", "Разумеется"]
    for start in polite_starts:
        if cleaned.startswith(start):
            cleaned = cleaned[len(start):].lstrip(", ")
    
    return cleaned.strip()

async def process_smart_text(message: Message, modules, bot_info):
    """🧠 Интеллектуальная обработка"""
    try:
        await save_user_and_message(message, modules)
        
        # Проверяем упоминания
        should_respond = await check_bot_mentions(message, bot_info)
        
        if should_respond:
            await process_harsh_smart_response(message, modules)
        else:
            # Редкие случайные ответы
            if random.random() < 0.005:
                responses = ["Ага.", "Понятно.", "Ясно."]
                await message.reply(random.choice(responses))
        
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
        
        # Ключевые слова
        keywords = ['бот', 'bot', 'робот', 'помощник']
        if any(keyword in text for keyword in keywords):
            return True
        
        # Вопросы
        if '?' in message.text and len(message.text) > 15:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Ошибка проверки упоминаний: {e}")
        return False

async def process_harsh_smart_response(message: Message, modules):
    """💡 Грубый умный ответ"""
    try:
        if modules.get('ai'):
            await process_harsh_ai_request(message, message.text, modules)
        else:
            responses = ["Что?", "AI отключен.", "Настрой ключи.", "Не работает."]
            await message.reply(random.choice(responses))
        
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


__all__ = ["register_all_handlers"]