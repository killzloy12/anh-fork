#!/usr/bin/env python3
"""
🎛️ HANDLERS INIT v2.0
Полная система обработчиков Enhanced Telegram Bot
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Sticker
from aiogram.filters import CommandStart, Command
from datetime import datetime

logger = logging.getLogger(__name__)


def register_all_handlers(dp, modules):
    """🎛️ Регистрация всех обработчиков"""
    
    router = Router()
    
    # Основные команды
    @router.message(CommandStart())
    async def start_handler(message: Message):
        user = message.from_user
        
        # Сохраняем пользователя
        if modules['db']:
            await modules['db'].save_user({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'language_code': user.language_code,
                'is_premium': getattr(user, 'is_premium', False)
            })
        
        welcome_text = (
            "🚀 <b>Enhanced Telegram Bot v2.0</b>\n\n"
            f"Привет, {user.first_name}! Добро пожаловать в продвинутого бота.\n\n"
            "✨ <b>Возможности:</b>\n"
            "🤖 /ai [вопрос] - AI помощник\n"
            "₿ /crypto bitcoin - Курсы криптовалют\n"
            "📊 /stats - Ваша статистика\n"
            "📈 /chart activity - Графики\n"
            "🎭 Анализ стикеров\n"
            "🛡️ Умная модерация\n\n"
            "💡 /help - Полная справка\n"
            "ℹ️ /about - О боте"
        )
        
        await message.answer(welcome_text)
        
        # Трекинг события
        if modules.get('analytics'):
            await modules['analytics'].track_user_action(
                user.id, message.chat.id, 'start_command'
            )
    
    @router.message(Command('help'))
    async def help_handler(message: Message):
        help_text = (
            "📖 <b>Справка Enhanced Telegram Bot v2.0</b>\n\n"
            "🤖 <b>AI Помощник:</b>\n"
            "/ai [вопрос] - Задать вопрос AI\n"
            "/memory_clear - Очистить память диалогов\n\n"
            "₿ <b>Криптовалюты:</b>\n"
            "/crypto bitcoin - Курс криптовалюты\n"
            "/crypto_trending - Трендовые монеты\n\n"
            "📊 <b>Аналитика:</b>\n"
            "/stats - Персональная статистика\n"
            "/dashboard - Детальный дашборд\n"
            "/export - Экспорт данных\n\n"
            "📈 <b>Графики:</b>\n"
            "/chart activity - График активности\n"
            "/chart emotions - График эмоций\n\n"
            "🎭 <b>Стикеры:</b>\n"
            "/sticker_stats - Статистика стикеров\n"
            "/emotions - Эмоциональный анализ\n\n"
            "🛡️ <b>Модерация (админы):</b>\n"
            "/moderation - Настройки модерации\n"
            "/ban [ID] - Забанить пользователя\n"
            "/warn [ID] - Предупредить пользователя\n\n"
            "ℹ️ <b>Информация:</b>\n"
            "/about - О боте\n"
            "/status - Статус системы"
        )
        
        await message.answer(help_text)
    
    @router.message(Command('about'))
    async def about_handler(message: Message):
        about_text = (
            "ℹ️ <b>Enhanced Telegram Bot v2.0</b>\n\n"
            "🎯 <b>Описание:</b>\n"
            "Продвинутый Telegram бот с искусственным интеллектом, "
            "аналитикой поведения и множеством полезных функций.\n\n"
            "⚡ <b>Технологии:</b>\n"
            "• Python 3.11+ с aiogram 3.8\n"
            "• AI: OpenAI GPT-4 + Anthropic Claude-3\n"
            "• База данных: SQLite с WAL режимом\n"
            "• Аналитика: Машинное обучение\n"
            "• Криптовалюты: CoinGecko API\n"
            "• Визуализация: matplotlib\n\n"
            "🧩 <b>Модули:</b>\n"
            "• Memory Module - Долгосрочная память\n"
            "• Behavior Module - Адаптивное поведение\n"
            "• Analytics Module - Детальная аналитика\n"
            "• Moderation Module - Автомодерация\n"
            "• Crypto Module - Криптовалютные данные\n"
            "• Stickers Module - Анализ стикеров\n"
            "• Charts Module - Графики и визуализация\n\n"
            f"⏰ <b>Время работы:</b> {datetime.now().strftime('%H:%M:%S')}\n"
            "🔧 <b>Версия:</b> 2.0 Complete Edition"
        )
        
        await message.answer(about_text)
    
    @router.message(Command('status'))
    async def status_handler(message: Message):
        user = message.from_user
        
        # Собираем статус модулей
        status_parts = []
        status_parts.append("🔥 <b>Статус Enhanced Telegram Bot v2.0</b>\n")
        
        # Проверяем модули
        modules_status = []
        
        if modules.get('ai'):
            ai_stats = modules['ai'].get_usage_stats()
            modules_status.append(f"🧠 AI: ✅ ({ai_stats.get('daily_usage', 0)} запросов)")
        else:
            modules_status.append("🧠 AI: ❌")
        
        if modules.get('crypto_service'):
            modules_status.append("₿ Crypto: ✅")
        else:
            modules_status.append("₿ Crypto: ❌")
        
        if modules.get('analytics_service'):
            modules_status.append("📊 Analytics: ✅")
        else:
            modules_status.append("📊 Analytics: ❌")
        
        if modules.get('memory'):
            modules_status.append("🧠 Memory: ✅")
        else:
            modules_status.append("🧠 Memory: ❌")
        
        status_parts.append("\n".join(modules_status))
        
        status_parts.append(f"\n⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        status_parts.append(f"👤 <b>Ваш ID:</b> {user.id}")
        
        await message.answer("\n\n".join(status_parts))
    
    # AI команды
    @router.message(Command('ai'))
    async def ai_handler(message: Message):
        if not modules.get('ai'):
            await message.answer("❌ AI сервис недоступен. Настройте API ключи в .env файле.")
            return
        
        user_message = message.text[4:].strip()  # Убираем "/ai "
        if not user_message:
            await message.answer("💡 Использование: /ai [ваш вопрос]\nПример: /ai Расскажи о Python")
            return
        
        try:
            # Получаем контекст памяти
            context = {}
            if modules.get('memory'):
                memory_context = await modules['memory'].get_context(message.from_user.id, message.chat.id)
                context.update(memory_context)
            
            # Получаем анализ поведения
            if modules.get('behavior'):
                behavior_analysis = await modules['behavior'].analyze_user_behavior(
                    message.from_user.id, message.chat.id, user_message, context
                )
                context['behavior_analysis'] = behavior_analysis
            
            # Генерируем ответ
            response = await modules['ai'].generate_response(
                user_message, message.from_user.id, context
            )
            
            # Адаптируем ответ под пользователя
            if modules.get('behavior') and context.get('behavior_analysis'):
                response = await modules['behavior'].adapt_response(
                    message.from_user.id, response, context['behavior_analysis']
                )
            
            await message.answer(response)
            
            # Сохраняем взаимодействие в память
            if modules.get('memory'):
                await modules['memory'].add_interaction(
                    message.from_user.id, message.chat.id, 
                    user_message, response
                )
            
            # Обучаем на взаимодействии
            if modules.get('behavior'):
                await modules['behavior'].learn_from_interaction(
                    message.from_user.id, message.chat.id, 
                    user_message, response
                )
            
        except Exception as e:
            logger.error(f"❌ Ошибка AI обработки: {e}")
            await message.answer("❌ Произошла ошибка при обращении к AI. Попробуйте позже.")
    
    @router.message(Command('memory_clear'))
    async def memory_clear_handler(message: Message):
        if not modules.get('memory'):
            await message.answer("❌ Модуль памяти недоступен")
            return
        
        success = await modules['memory'].clear_user_memory(
            message.from_user.id, message.chat.id
        )
        
        if success:
            await message.answer("🗑️ Память диалогов очищена")
        else:
            await message.answer("❌ Не удалось очистить память")
    
    # Криптовалютные команды
    @router.message(Command('crypto'))
    async def crypto_handler(message: Message):
        if not modules.get('crypto'):
            await message.answer("❌ Криптовалютный модуль недоступен")
            return
        
        coin_query = message.text[8:].strip()  # Убираем "/crypto "
        if not coin_query:
            await message.answer("💡 Использование: /crypto [название монеты]\nПример: /crypto bitcoin")
            return
        
        crypto_data = await modules['crypto'].handle_crypto_request(
            message.from_user.id, coin_query
        )
        
        if crypto_data.get('error'):
            await message.answer(f"❌ {crypto_data['message']}")
            return
        
        # Форматируем ответ
        response_parts = [
            f"₿ <b>{crypto_data['coin_name']} ({crypto_data['symbol']})</b>\n",
            f"💰 <b>Цена:</b> {crypto_data['price']}",
            f"📊 <b>Изменение 24ч:</b> {crypto_data['change_24h_formatted']} {crypto_data['trend_emoji']}",
            f"🏆 <b>Рейтинг:</b> #{crypto_data['market_cap_rank']}",
            f"💎 <b>Капитализация:</b> {crypto_data['market_cap']}",
            f"📦 <b>Объем торгов:</b> {crypto_data['volume_24h']}",
            f"⏰ <b>Обновлено:</b> {crypto_data['last_updated']}\n",
            f"📈 <b>Анализ:</b> {crypto_data['price_analysis']}"
        ]
        
        await message.answer("\n".join(response_parts))
    
    @router.message(Command('crypto_trending'))
    async def crypto_trending_handler(message: Message):
        if not modules.get('crypto'):
            await message.answer("❌ Криптовалютный модуль недоступен")
            return
        
        trending_data = await modules['crypto'].get_trending_crypto()
        
        if trending_data.get('error'):
            await message.answer(f"❌ {trending_data['message']}")
            return
        
        response_parts = ["🔥 <b>Трендовые криптовалюты:</b>\n"]
        
        for i, coin in enumerate(trending_data['trending_coins'], 1):
            response_parts.append(
                f"{i}. <b>{coin['name']} ({coin['symbol']})</b>\n"
                f"   💰 {coin['price']} ({coin['change_24h']})\n"
                f"   🏆 #{coin['market_cap_rank']} | 💎 {coin['market_cap']}"
            )
        
        response_parts.append(f"\n⏰ Обновлено: {trending_data['update_time']}")
        
        await message.answer("\n\n".join(response_parts))
    
    # Команды аналитики
    @router.message(Command('stats'))
    async def stats_handler(message: Message):
        if not modules.get('analytics'):
            await message.answer("❌ Модуль аналитики недоступен")
            return
        
        dashboard = await modules['analytics'].get_user_dashboard(message.from_user.id)
        
        if dashboard.get('error'):
            await message.answer(f"❌ {dashboard['error']}")
            return
        
        basic_stats = dashboard.get('basic_stats', {})
        
        response_parts = [
            f"📊 <b>Статистика пользователя {message.from_user.first_name}</b>\n",
            f"💬 <b>Сообщений:</b> {basic_stats.get('message_count', 0)}",
            f"📏 <b>Средняя длина:</b> {basic_stats.get('avg_message_length', 0)} символов",
            f"⚡ <b>Уровень активности:</b> {dashboard.get('activity_level', 'unknown')}",
            f"🎯 <b>Вовлеченность:</b> {int(dashboard.get('engagement_score', 0) * 100)}%",
            f"⏰ <b>Последняя активность:</b> {basic_stats.get('last_activity', 'Неизвестно')}\n"
        ]
        
        # Добавляем инсайты
        insights = dashboard.get('insights', [])
        if insights:
            response_parts.append("<b>💡 Персональные инсайты:</b>")
            for insight in insights:
                response_parts.append(f"• {insight}")
        
        await message.answer("\n".join(response_parts))
    
    # Обработка стикеров
    @router.message(F.sticker)
    async def sticker_handler(message: Message):
        sticker = message.sticker
        
        # Анализируем стикер
        if modules.get('stickers'):
            sticker_data = {
                'file_id': sticker.file_id,
                'set_name': sticker.set_name,
                'emoji': sticker.emoji,
                'is_animated': sticker.is_animated,
                'is_video': sticker.is_video
            }
            
            analysis = await modules['stickers'].analyze_sticker(
                message.from_user.id, message.chat.id, sticker_data
            )
            
            if not analysis.get('error'):
                emotion = analysis.get('emotion', 'neutral')
                if emotion != 'neutral':
                    emotion_responses = {
                        'happy': '😊 Вижу, у вас хорошее настроение!',
                        'sad': '😢 Надеюсь, все наладится!',
                        'angry': '😤 Понимаю ваши эмоции',
                        'love': '💕 Любовь - это прекрасно!',
                        'thinking': '🤔 О чем задумались?'
                    }
                    
                    response = emotion_responses.get(emotion, '👍 Отличный стикер!')
                    await message.answer(response)
        
        # Трекинг
        if modules.get('analytics'):
            await modules['analytics'].track_user_action(
                message.from_user.id, message.chat.id, 'sticker_sent',
                {'emoji': sticker.emoji, 'set_name': sticker.set_name}
            )
    
    # Обработка всех текстовых сообщений
    @router.message(F.text)
    async def text_handler(message: Message):
        user = message.from_user
        
        # Сохраняем пользователя и сообщение
        if modules.get('db'):
            await modules['db'].save_user({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'first_name': user.first_name,
                'last_name': user.last_name
            })
            
            await modules['db'].save_message({
                'message_id': message.message_id,
                'user_id': user.id,
                'chat_id': message.chat.id,
                'text': message.text,
                'message_type': 'text'
            })
        
        # Проверяем модерацию
        if modules.get('moderation'):
            moderation_result = await modules['moderation'].check_message(
                user.id, message.chat.id, message.text
            )
            
            if moderation_result['action'] != 'allow':
                action = moderation_result['action']
                reason = moderation_result['reason']
                
                if action == 'delete':
                    try:
                        await message.delete()
                        await message.answer(f"🛡️ Сообщение удалено: {reason}")
                    except:
                        await message.answer(f"⚠️ Обнаружено нарушение: {reason}")
                elif action == 'warn':
                    warnings = moderation_result.get('user_warnings', 0)
                    await message.answer(f"⚠️ Предупреждение ({warnings}): {reason}")
                elif action == 'timeout':
                    await message.answer(f"🕐 Временное ограничение: {reason}")
                
                return
        
        # Трекинг сообщений
        if modules.get('analytics'):
            await modules['analytics'].track_user_action(
                user.id, message.chat.id, 'message_sent',
                {'text_length': len(message.text)}
            )
        
        # Случайные ответы (если настроено)
        import random
        if (modules.get('config') and 
            random.random() < modules['config'].bot.random_reply_chance):
            
            random_responses = [
                "👍 Интересно!",
                "🤔 Понимаю",
                "✨ Спасибо за сообщение!",
                "💭 Хорошая мысль",
                "🎯 Согласен"
            ]
            
            await message.answer(random.choice(random_responses))
    
    # Регистрируем роутер
    dp.include_router(router)
    
    logger.info("🎛️ Все обработчики зарегистрированы")


__all__ = ["register_all_handlers"]