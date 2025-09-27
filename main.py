#!/usr/bin/env python3
"""
💀 ENHANCED TELEGRAM BOT v3.0 - ГРУБЫЙ РЕЖИМ С AI (ИСПРАВЛЕННЫЙ)
🔥 Максимально жесткая версия бота с человекоподобным AI

ИСПРАВЛЕНО:
• Правильные импорты модулей
• Обработка отсутствующих модулей
• Работа в базовом режиме без AI
• Постепенное подключение модулей
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
    print(f"ОШИБКА: Не найден модуль {e.name}")
    print("Используй config_harsh.py как config.py")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# Опциональные импорты модулей
modules_available = False
ai_modules_available = False

try:
    from app.services.ai_service import AIService
    from app.services.analytics_service import AnalyticsService 
    from app.services.crypto_service import CryptoService
    from app.modules.memory_module import MemoryModule
    from app.modules.moderation_module import ModerationModule
    from app.modules.analytics_module import AnalyticsModule
    from app.modules.behavior_module import BehaviorModule
    from app.modules.stickers_module import StickersModule
    from app.modules.crypto_module import CryptoModule
    from app.modules.charts_module import ChartsModule
    
    # Исправленные модули v3.0
    try:
        from app.modules.triggers_module_fixed import TriggersModule
    except ImportError:
        try:
            from app.modules.triggers_module import TriggersModule
        except ImportError:
            TriggersModule = None
    
    try:
        from app.modules.permissions_module_fixed import PermissionsModule
    except ImportError:
        try:
            from app.modules.permissions_module import PermissionsModule
        except ImportError:
            PermissionsModule = None
    
    modules_available = True
    
except ImportError as e:
    print(f"ПРЕДУПРЕЖДЕНИЕ: Базовый модуль {e.name} не найден")

# Попытка импорта AI модулей
try:
    # ИСПРАВЛЕННЫЕ ИМПОРТЫ - правильные пути к файлам
    from app.services.human_ai_service import HumanLikeAI, create_conversation_context
    from app.modules.conversation_memory import ConversationMemoryModule
    from app.modules.advanced_triggers import AdvancedTriggersModule
    from app.modules.media_triggers import MediaTriggersModule
    
    ai_modules_available = True
    print("✅ AI модули найдены!")
    
except ImportError as e:
    print(f"⚠️ AI модуль {e.name} не найден - работаем в базовом режиме")
    ai_modules_available = False

# ИСПРАВЛЕННЫЙ ИМПОРТ ОБРАБОТЧИКОВ
try:
    if ai_modules_available:
        from app.handlers.handlers_v3_fixed import register_all_handlers
        print("✅ Используем AI обработчики")
    else:
        from app.handlers.handlers_v3 import register_all_handlers
        print("⚠️ Используем базовые обработчики")
        
except ImportError as e:
    print(f"❌ Ошибка импорта обработчиков: {e}")
    print("Используем fallback обработчики")
    
    # Fallback - создаем простые обработчики
    def register_all_handlers(dp, modules):
        from app.handlers.handlers_v3_fixed import register_all_handlers as fallback_handlers
        return fallback_handlers(dp, modules)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def setup_bot_commands(bot: Bot):
    """⚙️ Настройка команд бота"""
    
    commands = [
        BotCommand(command="start", description="Запуск"),
        BotCommand(command="help", description="Команды"),
        BotCommand(command="ai", description="AI помощник"),
        BotCommand(command="crypto", description="Криптовалюты"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="about", description="О боте"),
    ]
    
    await bot.set_my_commands(commands)
    logger.info("⚙️ Команды настроены")

async def main():
    """💀 Основная функция ГРУБОГО запуска с AI"""
    
    print("💀 ENHANCED TELEGRAM BOT v3.0 - ЗАПУСК...")
    print("🧠 С поддержкой человекоподобного AI" if ai_modules_available else "⚠️ Базовый режим без AI")
    print("=" * 50)
    
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
            print("2. Скопируй содержимое из env_harsh.txt в .env")
            print("3. Заполни BOT_TOKEN и ADMIN_IDS")
            print("4. Обязательно укажи ALLOWED_CHAT_IDS!")
            input("Нажми Enter для выхода...")
            return
        
        if not config.bot.admin_ids:
            print("❌ ОШИБКА: ADMIN_IDS не указаны!")
            print("Укажи свой Telegram ID в .env файле")
            input("Нажми Enter для выхода...")
            return
        
        if not config.bot.allowed_chat_ids:
            print("⚠️ ВНИМАНИЕ: ALLOWED_CHAT_IDS не указаны!")
            print("Бот будет работать везде (небезопасно)")
            print("Рекомендуется указать разрешенные чаты")
        
        bot = Bot(
            token=config.bot.token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML
            )
        )
        
        dp = Dispatcher()
        
        print("💾 Инициализация базы данных...")
        db_service = DatabaseService(config.database)
        await db_service.initialize()
        
        # Инициализация модулей
        modules = {
            'config': config,
            'db': db_service,
            'bot': bot,
            'ai': None,
            'analytics_service': None,
            'crypto_service': None,
            'memory': None,
            'moderation': None,
            'analytics': None,
            'behavior': None,
            'stickers': None,
            'crypto': None,
            'charts': None,
            'triggers': None,
            'permissions': None,
            # Новые AI модули
            'human_ai': None,
            'conversation_memory': None,
            'advanced_triggers': None,
            'media_triggers': None
        }
        
        if modules_available:
            print("🧠 Инициализация базовых модулей...")
            if config.ai.openai_api_key or config.ai.anthropic_api_key:
                modules['ai'] = AIService(config)
                print("  ✅ AI активирован")
            else:
                print("  ❌ AI отключен (нет ключей)")
            
            print("📊 Инициализация аналитики...")
            modules['analytics_service'] = AnalyticsService(db_service)
            
            print("₿ Инициализация крипто...")
            if config.crypto.enabled:
                modules['crypto_service'] = CryptoService(config)
                print("  ✅ Крипто активировано")
            else:
                print("  ❌ Крипто отключено")
            
            print("🧩 Инициализация стандартных модулей...")
            modules['memory'] = MemoryModule(db_service)
            modules['moderation'] = ModerationModule(db_service, config) if config.moderation.enabled else None
            modules['analytics'] = AnalyticsModule(modules['analytics_service'])
            modules['behavior'] = BehaviorModule(db_service, modules['ai']) if modules['ai'] else None
            modules['stickers'] = StickersModule(db_service)
            modules['crypto'] = CryptoModule(modules['crypto_service']) if modules['crypto_service'] else None
            modules['charts'] = ChartsModule(db_service)
            
            if TriggersModule:
                modules['triggers'] = TriggersModule(db_service, config)
            
            if PermissionsModule:
                modules['permissions'] = PermissionsModule(config)
        
        # Инициализация AI модулей (если доступны)
        if ai_modules_available:
            print("🚀 Инициализация AI модулей...")
            
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
                logger.error(f"❌ Ошибка инициализации AI модулей: {e}")
                print(f"⚠️ AI модули частично недоступны: {e}")
        
        # Human-like AI
        if config.ai.openai_api_key or config.ai.anthropic_api_key:
                modules['ai'] = AIService(config)  # ← ДОБАВЬТЕ ЭТУ СТРОКУ!
                modules['human_ai'] = HumanLikeAI(config)
                print("  ✅ Human-like AI активирован")
        else:
             print("  ❌ OPENAI_API_KEY не найден в .env!")

        
        # ИСПРАВЛЕННАЯ РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
        print("🎛️ Регистрация обработчиков...")
        try:
            register_all_handlers(dp, modules)
            print("  ✅ Обработчики зарегистрированы")
        except Exception as e:
            logger.error(f"❌ Ошибка регистрации обработчиков: {e}")
            print(f"❌ Ошибка регистрации: {e}")
            return
        
        # Проверяем подключение
        print("📡 Проверка подключения...")
        try:
            bot_info = await bot.get_me()
            print(f"  💀 Подключен: @{bot_info.username}")
            print(f"  📝 Имя: {bot_info.first_name}")
            print(f"  🆔 ID: {bot_info.id}")
        except Exception as e:
            print(f"  ❌ ОШИБКА: {e}")
            print("Проверь BOT_TOKEN")
            input("Нажми Enter для выхода...")
            return
        
        # Настройка команд
        await setup_bot_commands(bot)
        
        # Уведомления админов
        if config.bot.admin_ids:
            mode_text = "🧠 ULTIMATE AI РЕЖИМ" if ai_modules_available else "⚠️ БАЗОВЫЙ РЕЖИМ"
            startup_message = (
                f"💀 **ENHANCED BOT v3.0 ЗАПУЩЕН!**\n\n"
                f"**Режим:** {mode_text}\n"
                f"**Бот:** @{bot_info.username}\n"
                f"**Разрешенных чатов:** {len(config.bot.allowed_chat_ids) if config.bot.allowed_chat_ids else 'Все'}\n\n"
            )
            
            if ai_modules_available:
                startup_message += (
                    "**🧠 AI ВОЗМОЖНОСТИ:**\n"
                    "• Человекоподобное общение\n"
                    "• Долгосрочная память диалогов\n"
                    "• Умные триггеры и реакции\n"
                    "• Анализ эмоций и контекста\n"
                    "• Мультимедийные ответы\n\n"
                )
            else:
                startup_message += (
                    "**⚠️ БАЗОВЫЙ РЕЖИМ:**\n"
                    "• Стандартное общение\n"
                    "• Базовые команды\n"
                    "• Простые триггеры\n\n"
                    "Для AI режима добавьте модули!\n\n"
                )
            
            startup_message += "**ГОТОВ К РАБОТЕ!**"
            
            for admin_id in config.bot.admin_ids:
                try:
                    await bot.send_message(admin_id, startup_message)
                    print(f"  📤 Админ уведомлен: {admin_id}")
                except Exception as e:
                    print(f"  ⚠️ Не удалось уведомить {admin_id}: {e}")
        
        print("\n" + "=" * 50)
        if ai_modules_available:
            print("🧠 ENHANCED AI BOT v3.0 УСПЕШНО ЗАПУЩЕН!")
            print("🚀 РЕЖИМ: МАКСИМАЛЬНО ЧЕЛОВЕКОПОДОБНЫЙ AI")
        else:
            print("💀 ENHANCED BOT v3.0 ЗАПУЩЕН В БАЗОВОМ РЕЖИМЕ")
            print("⚠️ Для AI режима добавьте модули!")
        print("=" * 50)
        
        if ai_modules_available:
            print("\n🧠 AI ОСОБЕННОСТИ:")
            print("  • Естественное человеческое общение")
            print("  • Долгосрочная память о пользователях")
            print("  • Анализ эмоций и адаптация")
            print("  • Умные реакции на стикеры/GIF")
            print("  • Расширенные триггеры с AI")
        else:
            print("\n🔧 БАЗОВЫЕ ВОЗМОЖНОСТИ:")
            print("  • Логирование всех сообщений")
            print("  • Ответы только при обращении")
            print("  • Работа в разрешенных чатах")
            print("  • Основные команды")
        
        if config.bot.allowed_chat_ids:
            print(f"\n🔒 РАЗРЕШЕННЫЕ ЧАТЫ: {config.bot.allowed_chat_ids}")
        else:
            print("\n⚠️ ВНИМАНИЕ: Нет ограничений по чатам!")
        
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
        print("  3. ALLOWED_CHAT_IDS в .env")
        print("  4. Правильность файлов конфигурации")
        print("  5. Наличие всех модулей")
        print("  6. Установку зависимостей: pip install anthropic aiofiles aiohttp")
        input("\nНажми Enter для выхода...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏸️ Остановка по запросу")
    except Exception as e:
        print(f"\n💥 Ошибка: {e}")
        input("Нажми Enter для выхода...")