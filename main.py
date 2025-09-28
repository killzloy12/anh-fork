#!/usr/bin/env python3
"""
💀 ENHANCED TELEGRAM BOT v3.0 - С ПРОИЗВОЛЬНЫМИ ПЕРСОНАЖАМИ И КАРМОЙ
🚀 Максимально крутая версия бота с AI персонажами

НОВОЕ В v3.0:
• Произвольные персонажи (/be описание)
• Система кармы с уровнями
• Улучшенный AI с персонажами
• Автоматическое начисление кармы
• Умная модерация
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == "win32":
    import locale
    import codecs
    
    try:
        locale.setlocale(locale.LC_ALL, '')
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    except:
        pass

sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

try:
    from config_harsh import load_config
    from database import DatabaseService
except ImportError as e:
    print(f"❌ ОШИБКА: Не найден модуль {e.name}")
    print("Используй config_harsh.py как config.py")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# ИМПОРТ AI МОДУЛЕЙ (НОВОЕ!)
try:
    from app.services.human_ai_service import HumanLikeAI, create_conversation_context
    from app.modules.conversation_memory import ConversationMemoryModule
    from app.modules.advanced_triggers import AdvancedTriggersModule
    from app.modules.media_triggers import MediaTriggersModule
    AI_MODULES_AVAILABLE = True
    print("✅ AI модули найдены!")
except ImportError as e:
    print(f"⚠️ AI модуль {e.name} не найден")
    AI_MODULES_AVAILABLE = False

# ИМПОРТ НОВЫХ СИСТЕМ (ПЕРСОНАЖИ И КАРМА)
try:
    from app.modules.custom_personality_system import CustomPersonalityManager
    from app.modules.karma_system import KarmaManager
    PERSONA_KARMA_AVAILABLE = True
    print("✅ Системы персонажей и кармы найдены!")
except ImportError as e:
    print(f"⚠️ Модуль {e.name} не найден")
    PERSONA_KARMA_AVAILABLE = False

# ИМПОРТ ОБРАБОТЧИКОВ
try:
    from app.handlers.handlers_v3_fixed import register_all_handlers
    print("✅ Обработчики найдены")
except ImportError as e:
    print(f"❌ Ошибка импорта обработчиков: {e}")
    print("Проверьте наличие файла handlers_v3_fixed.py")
    sys.exit(1)

# ОПЦИОНАЛЬНЫЕ СЕРВИСЫ
try:
    from app.services.ai_service import AIService
    from app.services.analytics_service import AnalyticsService 
    from app.services.crypto_service import CryptoService
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Сервис {e.name} не найден")
    SERVICES_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

async def setup_bot_commands(bot: Bot):
    """⚙️ Настройка команд бота"""
    
    commands = [
        BotCommand(command="start", description="🚀 Запуск бота"),
        BotCommand(command="help", description="📖 Все команды"),
        BotCommand(command="be", description="🎭 Стать персонажем"),
        BotCommand(command="karma", description="⚖️ Моя карма"),
        BotCommand(command="ai", description="🧠 AI помощник"),
        BotCommand(command="my_personas", description="👤 Мои персонажи"),
        BotCommand(command="karma_top", description="🏆 Топ кармы"),
        BotCommand(command="reset_persona", description="🔄 Сбросить персонажа"),
    ]
    
    await bot.set_my_commands(commands)
    logger.info("⚙️ Команды настроены")

async def main():
    """🚀 Основная функция запуска бота"""
    
    print("🎭 ENHANCED TELEGRAM BOT v3.0 - ПЕРСОНАЖИ И КАРМА")
    print("🧠 С поддержкой произвольных персонажей и системой кармы")
    print("=" * 60)
    
    try:
        # Создаем директории
        directories = [
            'data/logs', 'data/charts', 'data/exports', 'data/backups',
            'data/triggers', 'data/moderation', 'app/services', 'app/modules', 'app/handlers'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Логирование в файл
        file_handler = logging.FileHandler('data/logs/bot.log', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(file_handler)
        
        config = load_config()
        
        if not config.bot.token:
            print("❌ ОШИБКА: BOT_TOKEN не найден!")
            print("1. Создай файл .env")
            print("2. Заполни BOT_TOKEN и ADMIN_IDS")
            input("Нажми Enter для выхода...")
            return
        
        if not config.bot.admin_ids:
            print("❌ ОШИБКА: ADMIN_IDS не указаны!")
            input("Нажми Enter для выхода...")
            return
        
        bot = Bot(
            token=config.bot.token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        
        dp = Dispatcher()
        
        print("💾 Инициализация базы данных...")
        db_service = DatabaseService(config.database)
        await db_service.initialize()
        
        # МОДУЛИ
        modules = {
            'config': config,
            'db': db_service,
            'bot': bot
        }
        
        # БАЗОВЫЕ СЕРВИСЫ
        if SERVICES_AVAILABLE:
            print("🧠 Инициализация AI сервиса...")
            if config.ai.openai_api_key or config.ai.anthropic_api_key:
                modules['ai'] = AIService(config)
                print("  ✅ AI сервис активирован")
            else:
                print("  ⚠️ AI сервис отключен (нет ключей)")
            
            print("📊 Инициализация аналитики...")
            modules['analytics_service'] = AnalyticsService(db_service)
            
            print("₿ Инициализация крипто...")
            if config.crypto.enabled:
                modules['crypto_service'] = CryptoService(config)
                print("  ✅ Крипто активировано")
        
        # AI МОДУЛИ (ЧЕЛОВЕКОПОДОБНЫЙ AI)
        if AI_MODULES_AVAILABLE:
            print("🚀 Инициализация человекоподобного AI...")
            
            try:
                # Human-like AI
                modules['human_ai'] = HumanLikeAI(config)
                print("  ✅ Human-like AI активирован")
                
                # Память диалогов
                modules['conversation_memory'] = ConversationMemoryModule(db_service)
                await modules['conversation_memory'].initialize()
                print("  ✅ Память диалогов активирована")
                
                # Расширенные триггеры
                modules['advanced_triggers'] = AdvancedTriggersModule(
                    db_service, config, modules.get('ai')
                )
                await modules['advanced_triggers'].initialize()
                print("  ✅ Расширенные триггеры активированы")
                
                # Медиа триггеры
                modules['media_triggers'] = MediaTriggersModule(
                    db_service, config, bot
                )
                await modules['media_triggers'].initialize()
                print("  ✅ Медиа триггеры активированы")
                
            except Exception as e:
                logger.error(f"❌ Ошибка AI модулей: {e}")
                print(f"⚠️ AI модули частично недоступны: {e}")
        
        # НОВЫЕ СИСТЕМЫ (ПЕРСОНАЖИ И КАРМА)
        if PERSONA_KARMA_AVAILABLE:
            print("🎭 Инициализация системы персонажей...")
            try:
                modules['custom_personality_manager'] = CustomPersonalityManager(
                    db_service, config, modules.get('ai')
                )
                await modules['custom_personality_manager'].initialize()
                print("  ✅ Система персонажей активирована")
            except Exception as e:
                logger.error(f"❌ Ошибка персонажей: {e}")
            
            print("⚖️ Инициализация системы кармы...")
            try:
                modules['karma_manager'] = KarmaManager(db_service, config)
                await modules['karma_manager'].initialize()
                print("  ✅ Система кармы активирована")
            except Exception as e:
                logger.error(f"❌ Ошибка кармы: {e}")
        
        # РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
        print("🎛️ Регистрация обработчиков...")
        try:
            register_all_handlers(dp, modules)
            print("  ✅ Обработчики зарегистрированы")
        except Exception as e:
            logger.error(f"❌ Ошибка регистрации: {e}")
            print(f"❌ Ошибка регистрации: {e}")
            return
        
        # ПРОВЕРКА ПОДКЛЮЧЕНИЯ
        print("📡 Проверка подключения...")
        try:
            bot_info = await bot.get_me()
            print(f"  🤖 Подключен: @{bot_info.username}")
            print(f"  📝 Имя: {bot_info.first_name}")
            print(f"  🆔 ID: {bot_info.id}")
        except Exception as e:
            print(f"  ❌ ОШИБКА: {e}")
            print("Проверь BOT_TOKEN")
            return
        
        # Настройка команд
        await setup_bot_commands(bot)
        
        # УВЕДОМЛЕНИЯ АДМИНОВ
        if config.bot.admin_ids:
            features = []
            
            if AI_MODULES_AVAILABLE:
                features.append("🧠 Человекоподобный AI")
            if PERSONA_KARMA_AVAILABLE:
                features.append("🎭 Произвольные персонажи")
                features.append("⚖️ Система кармы")
            if SERVICES_AVAILABLE:
                features.append("📊 Аналитика")
                features.append("₿ Криптовалюты")
            
            startup_message = (
                f"🎭 **BOT v3.0 ЗАПУЩЕН!**\n\n"
                f"**Бот:** @{bot_info.username}\n"
                f"**Возможности:**\n"
            )
            
            for feature in features:
                startup_message += f"• {feature}\n"
            
            startup_message += (
                f"\n**🎯 Новые команды:**\n"
                f"• `/be описание` - стать персонажем\n"
                f"• `/karma` - моя карма\n"
                f"• `/karma_top` - топ по карме\n"
                f"• `/my_personas` - мои персонажи\n\n"
                f"**ГОТОВ К РАБОТЕ!**"
            )
            
            for admin_id in config.bot.admin_ids:
                try:
                    await bot.send_message(admin_id, startup_message)
                    print(f"  📤 Админ уведомлен: {admin_id}")
                except Exception as e:
                    print(f"  ⚠️ Не удалось уведомить {admin_id}: {e}")
        
        print("\n" + "=" * 60)
        print("🎭 ENHANCED BOT v3.0 С ПЕРСОНАЖАМИ УСПЕШНО ЗАПУЩЕН!")
        
        if AI_MODULES_AVAILABLE and PERSONA_KARMA_AVAILABLE:
            print("🚀 РЕЖИМ: МАКСИМАЛЬНЫЕ ВОЗМОЖНОСТИ")
            print("\n🎭 НОВЫЕ ВОЗМОЖНОСТИ:")
            print("  • Произвольные персонажи (/be описание)")
            print("  • Система кармы с 7 уровнями")
            print("  • AI отвечает в роли персонажа")
            print("  • Автоматическое начисление кармы")
            print("  • Умная модерация с кармой")
        elif AI_MODULES_AVAILABLE:
            print("🧠 РЕЖИМ: ЧЕЛОВЕКОПОДОБНЫЙ AI")
        else:
            print("⚠️ РЕЖИМ: БАЗОВЫЙ")
        
        print("=" * 60)
        
        if config.bot.allowed_chat_ids:
            print(f"\n🔒 РАЗРЕШЕННЫЕ ЧАТЫ: {config.bot.allowed_chat_ids}")
        
        print("\n💡 Для остановки: Ctrl+C")
        
        try:
            await dp.start_polling(bot, skip_updates=True)
        except KeyboardInterrupt:
            print("\n⏸️ Остановка...")
        finally:
            print("🛑 Остановка бота...")
            
            # Закрытие сервисов
            if modules.get('crypto_service'):
                await modules['crypto_service'].close()
            if modules.get('db'):
                await modules['db'].close()
            await bot.session.close()
            
            print("✅ Бот остановлен")
    
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        print(f"💥 ОШИБКА: {e}")
        print("\n🔍 Проверь:")
        print("  1. BOT_TOKEN в .env")
        print("  2. ADMIN_IDS в .env") 
        print("  3. Наличие файлов модулей")
        input("\nНажми Enter для выхода...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏸️ Остановка по запросу")
    except Exception as e:
        print(f"\n💥 Ошибка: {e}")
        input("Нажми Enter для выхода...")