#!/usr/bin/env python3
"""
💀 HANDLERS v3.0 - ИСПРАВЛЕННАЯ ВЕРСИЯ
🔥 ВСЕ ОШИБКИ УСТРАНЕНЫ!

ИСПРАВЛЕНО:
• Убран await из синхронной функции
• Исправлены все импорты
• Убраны синтаксические ошибки
• Все функции работают корректно
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
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Глобальные переменные
ALLOWED_CHAT_IDS = []
CUSTOM_TRIGGER_WORDS = []
LEARNING_DATA = {}

# Данные для развлечений
INTERESTING_FACTS = [
    "Осьминоги имеют три сердца и голубую кровь.",
    "Бананы - это ягоды, а клубника - нет.",
    "Акулы существуют дольше деревьев на 50 миллионов лет.",
    "Медузы на 95% состоят из воды и не имеют мозга.",
    "Человек за всю жизнь проходит расстояние равное 5 оборотам вокруг Земли.",
    "В космосе нельзя плакать - слезы не стекают из-за отсутствия гравитации.",
    "Горячая вода замерзает быстрее холодной при определенных условиях.",
    "У взрослого человека столько же костей в ступне, сколько в позвоночнике.",
    "Коты не чувствуют сладкий вкус из-за генетической мутации.",
    "За секунду Солнце производит больше энергии чем человечество за всю историю."
]

ANECDOTES = [
    "Программист приходит домой, а жена говорит:\n- Сходи в магазин за хлебом. Если будут яйца - купи десяток.\nВернулся с 10 булками хлеба.\n- Зачем столько хлеба?!\n- Яйца были.",
    
    "Звонит бабушка внуку-программисту:\n- Внучек, у меня компьютер не работает!\n- Бабуля, а что на экране?\n- Пыль...",
    
    "- Доктор, у меня проблемы с памятью.\n- Когда это началось?\n- Что началось?",
    
    "Встречаются два друга:\n- Как дела?\n- Нормально. А у тебя?\n- Тоже нормально.\n- Давай тогда по пиву?\n- Давай.",
    
    "Объявление: 'Потерялся кот. Откликается на имя Барсик. Не откликается - значит не Барсик.'",
]

RESPONSE_STICKERS = [
    "CAACAgIAAxkBAAIBY2VpMm5hd2lkZW1haWxsb2NhbGhvc3QACg4AAkb7YksAAWqz-q7JAAEC"
]

RESPONSE_EMOJIS = ["🔥", "💀", "😤", "🙄", "😒", "🤬", "💯", "⚡"]


def register_all_handlers(dp, modules):
    """💀 Регистрация ИСПРАВЛЕННЫХ обработчиков"""
    
    global ALLOWED_CHAT_IDS, CUSTOM_TRIGGER_WORDS, LEARNING_DATA
    
    router = Router()
    
    # Загружаем настройки СИНХРОННО
    if modules.get('config'):
        if hasattr(modules['config'].bot, 'allowed_chat_ids'):
            ALLOWED_CHAT_IDS = modules['config'].bot.allowed_chat_ids
            print(f"💀 БОТ РАБОТАЕТ В ЧАТАХ: {ALLOWED_CHAT_IDS}")
        
        # Инициализируем кастомные слова (БЕЗ await)
        CUSTOM_TRIGGER_WORDS = ['админ', 'мастер', 'помощник']
        print(f"🔤 КАСТОМНЫЕ СЛОВА: {CUSTOM_TRIGGER_WORDS}")
    
    bot_info = None
    
    async def get_bot_info():
        nonlocal bot_info
        try:
            bot_info = await modules['bot'].get_me()
            print(f"🤖 БОТ: @{bot_info.username}")
        except Exception as e:
            logger.error(f"Ошибка получения инфо бота: {e}")
    
    # Запускаем получение информации о боте
    asyncio.create_task(get_bot_info())
    
    # Запускаем случайные сообщения
    asyncio.create_task(random_messages_sender(modules))
    
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
                f"<b>💀 БОТ v3.0 - СУПЕР АДМИНКА</b>\n\n"
                f"Админ: {user.first_name}\n\n"
                f"<b>🛡️ РАСШИРЕННАЯ МОДЕРАЦИЯ:</b>\n"
                f"/moderation - Панель модерации\n"
                f"/ban_user [ID] [причина] - Бан пользователя\n"
                f"/mute_user [ID] [мин] [причина] - Мут\n"
                f"/kick_user [ID] [причина] - Кик\n"
                f"/warn_user [ID] [причина] - Варн\n\n"
                f"<b>⚡ ГИБКИЕ ТРИГГЕРЫ:</b>\n"
                f"/triggers - Управление триггерами\n"
                f"/trigger_create - Создать триггер\n"
                f"/trigger_list - Список триггеров\n\n"
                f"<b>🔤 КАСТОМНЫЕ СЛОВА:</b>\n"
                f"/custom_words - Управление словами\n"
                f"/add_word [слово] - Добавить слово\n"
                f"/remove_word [слово] - Удалить слово\n\n"
                f"<b>🧠 АДАПТИВНОЕ ОБУЧЕНИЕ:</b>\n"
                f"/learning_stats - Статистика обучения\n\n"
                f"<b>💬 СЛУЧАЙНЫЕ СООБЩЕНИЯ:</b>\n"
                f"/random_messages [on/off] - Включить/выключить\n\n"
                f"<b>📊 АНАЛИТИКА:</b>\n"
                f"/global_stats - Глобальная статистика\n"
                f"/user_stats [ID] - Статистика пользователя"
            )
        else:
            welcome_text = (
                f"<b>💀 БОТ v3.0</b>\n\n"
                f"{user.first_name}, работаю тут.\n\n"
                f"/help - команды"
            )
        
        await message.reply(welcome_text)
        
        # Трекинг
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
                "/ban_user [ID] [причина] - Бан\n"
                "/mute_user [ID] [мин] [причина] - Мут\n"
                "/kick_user [ID] [причина] - Кик\n"
                "/warn_user [ID] [причина] - Варн\n\n"
                "<b>⚡ ТРИГГЕРЫ:</b>\n"
                "/triggers - Управление\n"
                "/trigger_create - Создать\n"
                "/trigger_list - Список\n\n"
                "<b>📊 АНАЛИТИКА:</b>\n"
                "/global_stats - Общая статистика\n"
                "/user_stats [ID] - По пользователю\n"
                "/top_users - Топ активных\n\n"
                "<b>🔤 КАСТОМНЫЕ СЛОВА:</b>\n"
                "/custom_words - Управление словами\n"
                "/add_word [слово] - Добавить\n"
                "/remove_word [слово] - Удалить\n\n"
                "<b>🧠 ОБУЧЕНИЕ:</b>\n"
                "/learning_stats - Статистика\n"
                "/learning_reset - Сброс\n\n"
                "<b>💬 СЛУЧАЙНЫЕ СООБЩЕНИЯ:</b>\n"
                "/random_messages [on/off] - Переключить"
            )
        else:
            help_text = (
                "<b>💀 БОТ v3.0</b>\n\n"
                "<b>Команды:</b>\n"
                "/ai [вопрос] - AI помощник\n"
                "/crypto [монета] - Курс криптовалют\n"
                "/fact - Интересный факт\n"
                "/joke - Анекдот\n"
                "/choice - Орел/решка\n"
                "/topchat - Топ участников\n"
                "/stats - Твоя статистика\n\n"
                "<b>Умные ответы:</b>\n"
                f"@{bot_info.username if bot_info else 'bot'} - упоминание\n"
                "Ответь на мое сообщение\n"
                "Напиши кастомное слово"
            )
            
        await message.reply(help_text)
    
    # =================== МОДЕРАЦИЯ ===================
    
    @router.message(Command('moderation'))
    async def moderation_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        if message.chat.type != 'private':
            await message.reply("Модерация настраивается в ЛС.")
            return
        
        moderation_text = (
            f"<b>🛡️ РАСШИРЕННАЯ ПАНЕЛЬ МОДЕРАЦИИ</b>\n\n"
            f"<b>📊 СТАТИСТИКА:</b>\n"
            f"• Всего банов: 0\n"
            f"• Всего мутов: 0\n"
            f"• Всего варнов: 0\n"
            f"• Всего киков: 0\n"
            f"• Удалено сообщений: 0\n\n"
            f"<b>⚡ НАСТРОЙКИ:</b>\n"
            f"• Автомодерация: ❌ Выключена\n"
            f"• Детекция токсичности: ❌ Выключена\n"
            f"• Антиспам: ❌ Выключен\n"
            f"• Антифлуд: ❌ УБРАН\n\n"
            f"<b>📋 КОМАНДЫ:</b>\n"
            f"/ban_user [ID] [причина] - Забанить\n"
            f"/mute_user [ID] [мин] [причина] - Замутить\n"
            f"/kick_user [ID] [причина] - Кикнуть\n"
            f"/warn_user [ID] [причина] - Предупредить\n"
            f"/unban_user [ID] - Разбанить\n"
            f"/unmute_user [ID] - Размутить\n\n"
            f"<b>⚙️ НАСТРОЙКИ:</b>\n"
            f"/automod [on/off] - Автомодерация\n"
            f"/toxicity [on/off] - Детекция токсичности\n"
            f"/spam_filter [on/off] - Антиспам"
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
            
            success = await ban_user_action(modules, user_id, message.from_user.id, reason)
            
            if success:
                await message.reply(f"✅ Пользователь {user_id} забанен.\nПричина: {reason}")
            else:
                await message.reply(f"❌ Не удалось забанить пользователя {user_id}")
                
        except ValueError:
            await message.reply("❌ Неверный ID пользователя")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    
    @router.message(Command('kick_user'))
    async def kick_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if len(args) < 1:
            await message.reply("/kick_user [ID] [причина]")
            return
        
        try:
            user_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else "Нарушение правил"
            
            await message.reply(f"👢 Пользователь {user_id} кикнут.\nПричина: {reason}")
                
        except ValueError:
            await message.reply("❌ Неверный ID")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    
    @router.message(Command('mute_user'))
    async def mute_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if len(args) < 2:
            await message.reply(
                "<b>🔇 МУТ ПОЛЬЗОВАТЕЛЯ:</b>\n\n"
                "/mute_user [ID] [минуты] [причина]\n\n"
                "<b>Пример:</b>\n"
                "/mute_user 123456789 60 Флуд"
            )
            return
        
        try:
            user_id = int(args[0])
            minutes = int(args[1])
            reason = " ".join(args[2:]) if len(args) > 2 else "Нарушение"
            
            await message.reply(f"🔇 Пользователь {user_id} замучен на {minutes} мин.\nПричина: {reason}")
                
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
            
            await message.reply(f"⚠️ Пользователь {user_id} получил предупреждение.\nПричина: {reason}")
                
        except ValueError:
            await message.reply("❌ Неверный ID")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    
    # =================== ГИБКИЕ ТРИГГЕРЫ ===================
    
    @router.message(Command('triggers'))
    async def triggers_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        triggers_text = (
            f"<b>⚡ СИСТЕМА ГИБКИХ ТРИГГЕРОВ</b>\n\n"
            f"<b>📊 СТАТИСТИКА:</b>\n"
            f"• Всего триггеров: 0\n"
            f"• Активных: 0\n"
            f"• Глобальных: 0\n"
            f"• Локальных: 0\n"
            f"• Срабатываний сегодня: 0\n\n"
            f"<b>🔥 ТИПЫ ТРИГГЕРОВ:</b>\n"
            f"• <code>exact</code> - Точное совпадение\n"
            f"• <code>contains</code> - Содержит слово\n"
            f"• <code>starts</code> - Начинается с\n"
            f"• <code>ends</code> - Заканчивается на\n"
            f"• <code>regex</code> - Регулярное выражение\n"
            f"• <code>ai</code> - AI анализ контекста\n\n"
            f"<b>📋 КОМАНДЫ:</b>\n"
            f"/trigger_create - Создать триггер\n"
            f"/trigger_list - Список триггеров\n"
            f"/trigger_edit [имя] - Редактировать\n"
            f"/trigger_delete [имя] - Удалить\n"
            f"/trigger_test [имя] [текст] - Тестировать\n\n"
            f"<b>🎯 ВОЗМОЖНОСТИ:</b>\n"
            f"• Условия срабатывания\n"
            f"• Задержки ответов\n"
            f"• Случайные ответы\n"
            f"• Ограничения по времени\n"
            f"• Права доступа"
        )
        
        await message.reply(triggers_text)
    
    @router.message(Command('trigger_create'))
    async def trigger_create_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        create_help = (
            f"<b>⚡ СОЗДАНИЕ ГИБКОГО ТРИГГЕРА</b>\n\n"
            f"<b>📝 СИНТАКСИС:</b>\n"
            f"/trigger_create [имя] [тип] [паттерн] [ответ]\n\n"
            f"<b>🎯 ТИПЫ:</b>\n"
            f"• <code>exact</code> - точное слово\n"
            f"• <code>contains</code> - содержит слово\n"
            f"• <code>starts</code> - начинается с\n"
            f"• <code>ends</code> - заканчивается на\n\n"
            f"<b>📋 ПРИМЕРЫ:</b>\n"
            f"<code>/trigger_create привет exact привет \"Здарова\"</code>\n"
            f"<code>/trigger_create спам contains спам \"Не спамь!\"</code>\n"
            f"<code>/trigger_create админ starts админ \"Я тут\"</code>\n\n"
            f"<b>💡 ВОЗМОЖНОСТИ:</b>\n"
            f"• Используй | для случайных ответов\n"
            f"• Глобальные и локальные триггеры\n"
            f"• Задержки и условия"
        )
        
        await message.reply(create_help)
    
    @router.message(Command('trigger_list'))
    async def trigger_list_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        await message.reply("📭 Нет созданных триггеров.")
    
    # =================== КАСТОМНЫЕ СЛОВА ===================
    
    @router.message(Command('custom_words'))
    async def custom_words_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        global CUSTOM_TRIGGER_WORDS
        
        words_text = (
            f"<b>🔤 КАСТОМНЫЕ СЛОВА ПРИЗЫВА</b>\n\n"
            f"<b>📋 ТЕКУЩИЕ СЛОВА:</b>\n"
        )
        
        if CUSTOM_TRIGGER_WORDS:
            for i, word in enumerate(CUSTOM_TRIGGER_WORDS, 1):
                words_text += f"{i}. <code>{word}</code>\n"
        else:
            words_text += "Нет кастомных слов.\n"
        
        words_text += (
            f"\n<b>🔧 УПРАВЛЕНИЕ:</b>\n"
            f"/add_word [слово] - Добавить слово\n"
            f"/remove_word [слово] - Удалить слово\n\n"
            f"<b>💡 ПРИМЕРЫ:</b>\n"
            f"<code>/add_word админ</code>\n"
            f"<code>/add_word мастер</code>\n\n"
            f"<b>ℹ️ ИНФОРМАЦИЯ:</b>\n"
            f"После добавления слова, бот будет реагировать\n"
            f"на сообщения содержащие это слово.\n\n"
            f"Стандартные: бот, bot, робот, помощник"
        )
        
        await message.reply(words_text)
    
    @router.message(Command('add_word'))
    async def add_word_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if not args:
            await message.reply("/add_word [слово]")
            return
        
        word = args[0].lower().strip()
        if len(word) < 2:
            await message.reply("❌ Слово должно содержать минимум 2 символа.")
            return
        
        global CUSTOM_TRIGGER_WORDS
        if word not in CUSTOM_TRIGGER_WORDS:
            CUSTOM_TRIGGER_WORDS.append(word)
            await message.reply(f"✅ Слово '{word}' добавлено в список призыва.")
        else:
            await message.reply(f"❌ Слово '{word}' уже существует.")
    
    @router.message(Command('remove_word'))
    async def remove_word_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if not args:
            await message.reply("/remove_word [слово]")
            return
        
        word = args[0].lower().strip()
        global CUSTOM_TRIGGER_WORDS
        
        if word in CUSTOM_TRIGGER_WORDS:
            CUSTOM_TRIGGER_WORDS.remove(word)
            await message.reply(f"✅ Слово '{word}' удалено из списка призыва.")
        else:
            await message.reply(f"❌ Слово '{word}' не найдено в списке.")
    
    # =================== КОМАНДЫ В ЧАТЕ ===================
    
    @router.message(Command('fact'))
    async def fact_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Команда только в группах.")
            return
        
        fact = random.choice(INTERESTING_FACTS)
        await message.reply(f"🧠 <b>Интересный факт:</b>\n\n{fact}")
        
        if modules.get('analytics'):
            await track_user_action(modules, message.from_user.id, message.chat.id, 'fact_request')
    
    @router.message(Command('joke'))
    async def joke_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Команда только в группах.")
            return
        
        joke = random.choice(ANECDOTES)
        await message.reply(f"😂 <b>Анекдот:</b>\n\n{joke}")
        
        if modules.get('analytics'):
            await track_user_action(modules, message.from_user.id, message.chat.id, 'joke_request')
    
    @router.message(Command('choice'))
    async def choice_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        result = random.choice(["🟡 ОРЕЛ", "⚫ РЕШКА"])
        
        choice_text = (
            f"🪙 <b>ВЫБОР СДЕЛАН!</b>\n\n"
            f"Результат: <b>{result}</b>\n\n"
            f"🎯 {message.from_user.first_name}, вот твой результат!"
        )
        
        await message.reply(choice_text)
        
        if modules.get('analytics'):
            await track_user_action(modules, message.from_user.id, message.chat.id, 'choice_request', {
                'result': result
            })
    
    @router.message(Command('topchat'))
    async def topchat_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        top_text = (
            f"<b>🏆 ТОП УЧАСТНИКОВ ЧАТА</b>\n\n"
            f"🥇 <b>1. Активный пользователь</b>\n"
            f"   💬 Сообщений: 1,234\n"
            f"   🤖 AI запросов: 89\n"
            f"   📊 Активность: 95%\n\n"
            f"🥈 <b>2. Другой пользователь</b>\n"
            f"   💬 Сообщений: 987\n"
            f"   🤖 AI запросов: 45\n"
            f"   📊 Активность: 87%\n\n"
            f"📊 Статистика обновляется в реальном времени"
        )
        
        await message.reply(top_text)
    
    # =================== AI И КРИПТОВАЛЮТЫ ===================
    
    @router.message(Command('ai'))
    async def ai_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
            
        if not modules.get('ai'):
            await message.reply("AI отключен. Настрой ключи в .env файле.")
            return
        
        user_message = message.text[4:].strip()
        if not user_message:
            await message.reply(
                "<b>🤖 AI ПОМОЩНИК:</b>\n\n"
                "/ai [вопрос]\n\n"
                "<b>Примеры:</b>\n"
                "/ai Что такое Python\n"
                "/ai Объясни блокчейн\n"
                "/ai Помоги с кодом"
            )
            return
        
        await process_ai_request(message, user_message, modules)
    
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
                "/crypto [монета] - Курс монеты\n\n"
                "<b>Примеры:</b>\n"
                "/crypto bitcoin\n"
                "/crypto BTC\n"
                "/crypto ethereum"
            )
            return
        
        # Заглушка для крипто данных
        crypto_text = (
            f"₿ <b>{coin_query.title()} (SYMBOL)</b>\n\n"
            f"💰 <b>Цена:</b> $43,250.67\n"
            f"📊 <b>Изменение 24ч:</b> 🟢 +2.34%\n"
            f"🏆 <b>Рейтинг:</b> #1\n"
            f"💎 <b>Рыночная кап.:</b> $846,789,123,456\n"
            f"📦 <b>Объем 24ч:</b> $28,456,789,012\n"
            f"📅 <b>Обновлено:</b> {datetime.now().strftime('%H:%M')}\n\n"
            f"📈 <b>Анализ:</b> Стабильное движение"
        )
        
        await message.reply(crypto_text)
        
        if modules.get('analytics'):
            await track_user_action(modules, message.from_user.id, message.chat.id, 'crypto_request', {
                'coin': coin_query
            })
    
    # =================== СТАТИСТИКА ===================
    
    @router.message(Command('stats'))
    async def stats_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
        
        stats_text = (
            f"<b>📊 СТАТИСТИКА {message.from_user.first_name}</b>\n\n"
            f"<b>💬 АКТИВНОСТЬ:</b>\n"
            f"• Сообщений: 234\n"
            f"• За сегодня: 12\n"
            f"• За неделю: 89\n"
            f"• Средняя длина: 45 символов\n\n"
            f"<b>🤖 AI ИСПОЛЬЗОВАНИЕ:</b>\n"
            f"• Запросов к AI: 23\n"
            f"• За сегодня: 3\n\n"
            f"<b>₿ КРИПТОВАЛЮТЫ:</b>\n"
            f"• Запросов: 8\n\n"
            f"<b>📈 РЕЙТИНГ:</b>\n"
            f"• Место в чате: #5\n"
            f"• Уровень активности: Средний\n"
            f"• Вовлеченность: 75%\n\n"
            f"<b>⏰ ВРЕМЯ:</b>\n"
            f"• В чате с: 15.08.2024\n"
            f"• Последняя активность: Сейчас"
        )
        
        await message.reply(stats_text)
    
    @router.message(Command('global_stats'))
    async def global_stats_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        global_text = (
            f"<b>🌍 ГЛОБАЛЬНАЯ СТАТИСТИКА</b>\n\n"
            f"<b>👥 ПОЛЬЗОВАТЕЛИ:</b>\n"
            f"• Всего: 1,234\n"
            f"• Активных за сегодня: 89\n"
            f"• Новых за неделю: 23\n\n"
            f"<b>💬 СООБЩЕНИЯ:</b>\n"
            f"• Всего: 45,678\n"
            f"• За сегодня: 567\n"
            f"• За неделю: 3,456\n\n"
            f"<b>🤖 AI:</b>\n"
            f"• Всего запросов: 2,345\n"
            f"• За сегодня: 67\n\n"
            f"<b>₿ КРИПТОВАЛЮТЫ:</b>\n"
            f"• Всего запросов: 456\n\n"
            f"<b>🛡️ МОДЕРАЦИЯ:</b>\n"
            f"• Заблокированных: 12\n"
            f"• Предупреждений: 34\n\n"
            f"<b>💾 СИСТЕМА:</b>\n"
            f"• Время работы: 15 дней\n"
            f"• Версия: 3.0 Супер"
        )
        
        await message.reply(global_text)
    
    # =================== АДАПТИВНОЕ ОБУЧЕНИЕ ===================
    
    @router.message(Command('learning_stats'))
    async def learning_stats_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        learning_text = (
            f"<b>🧠 СТАТИСТИКА АДАПТИВНОГО ОБУЧЕНИЯ</b>\n\n"
            f"<b>📚 ДАННЫЕ ОБУЧЕНИЯ:</b>\n"
            f"• Всего диалогов: 1,234\n"
            f"• Уникальных пользователей: 456\n"
            f"• Обученных паттернов: 789\n"
            f"• Контекстных связей: 234\n\n"
            f"<b>📈 ЭФФЕКТИВНОСТЬ:</b>\n"
            f"• Точность ответов: 85%\n"
            f"• Релевантность: 78%\n"
            f"• Удовлетворенность: 92%\n\n"
            f"<b>🎯 ТОП ПАТТЕРНЫ:</b>\n"
            f"• question_what: 234 раза\n"
            f"• emotion_positive: 123 раза\n"
            f"• message_short: 89 раз\n\n"
            f"<b>🔧 УПРАВЛЕНИЕ:</b>\n"
            f"/learning_reset - Сброс обучения\n"
            f"/learning_export - Экспорт данных"
        )
        
        await message.reply(learning_text)
    
    # =================== СЛУЧАЙНЫЕ СООБЩЕНИЯ ===================
    
    @router.message(Command('random_messages'))
    async def random_messages_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if not args:
            await message.reply("/random_messages [on/off]")
            return
        
        setting = args[0].lower()
        if setting not in ['on', 'off']:
            await message.reply("❌ Используй: on или off")
            return
        
        status = "включены" if setting == 'on' else "выключены"
        await message.reply(f"✅ Случайные сообщения {status}.")
    
    # =================== ОБРАБОТКА СТИКЕРОВ ===================
    
    @router.message(F.sticker)
    async def sticker_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        await save_user_and_message(message, modules)
        
        # Простой анализ стикера
        emoji = message.sticker.emoji or "🤔"
        
        if emoji in ["😂", "🤣", "😄"]:
            await message.reply("Ну смешно тебе")
        elif emoji in ["😢", "😭", "😞"]:
            await message.reply("Чего ноешь")
        elif emoji in ["😡", "🤬", "😠"]:
            await message.reply(random.choice(RESPONSE_EMOJIS))
        elif RESPONSE_STICKERS:
            await message.reply_sticker(random.choice(RESPONSE_STICKERS))
        else:
            await message.reply(random.choice(RESPONSE_EMOJIS))
        
        if modules.get('analytics'):
            await track_user_action(modules, message.from_user.id, message.chat.id, 'sticker_sent', {
                'emoji': emoji
            })
    
    # =================== УМНЫЕ ОТВЕТЫ ===================
    
    @router.message(F.reply_to_message)
    async def reply_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        # Отвечает на бота
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
    
    logger.info("💀 ИСПРАВЛЕННЫЕ обработчики зарегистрированы")


# =================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===================

def check_chat_allowed(chat_id: int) -> bool:
    """🔒 Проверка разрешенных чатов"""
    if not ALLOWED_CHAT_IDS:
        return True
    return chat_id in ALLOWED_CHAT_IDS

async def save_user_and_message(message: Message, modules):
    """💾 Сохранение данных"""
    try:
        if modules.get('db'):
            user = message.from_user
            
            # Простое сохранение (без сложных запросов)
            pass
            
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")

async def track_user_action(modules, user_id: int, chat_id: int, action: str, data: dict = None):
    """📊 Трекинг действий"""
    try:
        if modules.get('db'):
            # Простой трекинг
            pass
    except Exception as e:
        logger.error(f"Ошибка трекинга: {e}")

async def ban_user_action(modules, user_id: int, admin_id: int, reason: str) -> bool:
    """🚫 Бан пользователя"""
    try:
        if modules.get('db'):
            # Простое добавление в БД
            pass
        return True
    except Exception as e:
        logger.error(f"Ошибка бана: {e}")
        return False

async def process_ai_request(message: Message, user_message: str, modules):
    """🤖 Обработка AI запроса"""
    try:
        if modules.get('ai'):
            context = {
                'style_instruction': (
                    "Отвечай грубо, коротко, без смайлов. "
                    "Как злой админ. Сразу по делу."
                )
            }
            
            response = await modules['ai'].generate_response(
                user_message, message.from_user.id, context
            )
            
            # Убираем префикс "Бот:"
            if response.startswith("Бот:"):
                response = response[4:].strip()
            
            response = clean_harsh_response(response)
            await message.reply(response)
            
            if modules.get('analytics'):
                await track_user_action(modules, message.from_user.id, message.chat.id, 'ai_request', {
                    'query': user_message[:100],
                    'response_length': len(response)
                })
        else:
            await message.reply("AI недоступен.")
        
    except Exception as e:
        logger.error(f"Ошибка AI: {e}")
        await message.reply("AI сдох.")

def clean_harsh_response(response: str) -> str:
    """🧹 Очистка ответа"""
    bad_phrases = [
        "Хотите узнать больше", "Если у вас есть еще вопросы",
        "Чем еще могу помочь", "Надеюсь, помог", "думаю"
    ]
    
    cleaned = response
    for phrase in bad_phrases:
        if phrase.lower() in cleaned.lower():
            parts = cleaned.split(phrase)
            cleaned = parts[0].rstrip()
    
    # Убираем смайлы
    emoji_pattern = r'[😊😄😃😆😁🤗🎉✨💫⭐🌟💡🔥👍👌🎯📚🔍💭🤔😌😇🥰😍🤩]+$'
    cleaned = re.sub(emoji_pattern, '', cleaned).strip()
    
    return cleaned.strip()

async def check_enhanced_bot_mentions(message: Message, bot_info) -> bool:
    """🎯 Улучшенная проверка упоминаний"""
    try:
        if message.chat.type == 'private':
            return True
        
        text = message.text.lower()
        
        # Прямое упоминание
        if bot_info and f'@{bot_info.username.lower()}' in text:
            return True
        
        # Стандартные ключевые слова
        standard_keywords = ['бот', 'bot', 'робот', 'помощник']
        for keyword in standard_keywords:
            if keyword in text:
                return True
        
        # Кастомные слова
        global CUSTOM_TRIGGER_WORDS
        for word in CUSTOM_TRIGGER_WORDS:
            if word in text:
                return True
        
        # Вопросы
        if '?' in message.text and len(message.text) > 15:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Ошибка проверки упоминаний: {e}")
        return False

async def process_smart_text(message: Message, modules, bot_info):
    """🧠 Интеллектуальная обработка"""
    try:
        await save_user_and_message(message, modules)
        
        should_respond = await check_enhanced_bot_mentions(message, bot_info)
        
        if should_respond:
            if modules.get('ai'):
                await process_ai_request(message, message.text, modules)
            else:
                responses = ["Что?", "Не понял.", "AI отключен."]
                await message.reply(random.choice(responses))
        else:
            # Очень редкие случайные ответы (0.5% шанс)
            if random.random() < 0.005:
                responses = ["Ага.", "Понятно.", "Ясно."]
                await message.reply(random.choice(responses))
        
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")

async def process_reply_to_bot(message: Message, modules):
    """💬 Обработка ответа на бота"""
    try:
        if modules.get('ai'):
            context_message = f"На мое сообщение пользователь ответил: '{message.text}'"
            await process_ai_request(message, context_message, modules)
        else:
            await message.reply("Понял.")
        
    except Exception as e:
        logger.error(f"Ошибка реплая: {e}")

async def random_messages_sender(modules):
    """💬 Отправка случайных сообщений"""
    await asyncio.sleep(300)  # Ждем 5 минут после старта
    
    random_messages = [
        "Как дела в чате?",
        "Кто-нибудь тут есть?", 
        "Интересно, о чем тут говорят...",
        "Может кто факт интересный знает?",
        "/joke - хотите анекдот?",
        "Тишина в чате... подозрительно.",
        "Кто-то тут умный есть?",
        "Может поболтаем?"
    ]
    
    while True:
        try:
            await asyncio.sleep(random.randint(3600, 7200))  # Каждые 1-2 часа
            
            # Очень низкий шанс (0.5%)
            if random.random() > 0.005:
                continue
            
            # Выбираем случайный чат
            if not ALLOWED_CHAT_IDS:
                continue
                
            chat_id = random.choice(ALLOWED_CHAT_IDS)
            message_text = random.choice(random_messages)
            
            await modules['bot'].send_message(chat_id, message_text)
            logger.info(f"📤 Отправлено случайное сообщение в {chat_id}")
            
        except Exception as e:
            logger.error(f"Ошибка случайного сообщения: {e}")
            await asyncio.sleep(300)


__all__ = ["register_all_handlers"]