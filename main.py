#!/usr/bin/env python3
"""
💀 ENHANCED TELEGRAM BOT v3.0 - ГРУБЫЙ РЕЖИМ
🔥 Максимально жесткая версия бота

ИСПРАВЛЕНО:
• Правильная регистрация обработчиков
• Работа только в разрешенных чатах
• Логирование всех сообщений
• Ответы только на обращения, команды и реплеи
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
    
    # ИСПРАВЛЕННЫЙ ИМПОРТ ОБРАБОТЧИКОВ
    from app.handlers.handlers_v3 import register_all_handlers
    
    modules_available = True
    
except ImportError as e:
    print(f"ПРЕДУПРЕЖДЕНИЕ: Модуль {e.name} не найден")
    print("Бот будет работать в базовом режиме")
    
    # Используем базовые обработчики если модули недоступны
    def register_all_handlers(dp, modules):
        from app.handlers.handlers_v3 import register_basic_handlers
        register_basic_handlers(dp, modules)

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
    
    # ТОЛЬКО ОСНОВНЫЕ КОМАНДЫ, БЕЗ АДМИНСКИХ
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
    """💀 Основная функция ГРУБОГО запуска"""
    
    print("💀 ГРУБЫЙ TELEGRAM BOT v3.0 - ЗАПУСК...")
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
            'permissions': None
        }
        
        if modules_available:
            print("🧠 Инициализация AI...")
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
            
            print("🧩 Инициализация модулей...")
            modules['memory'] = MemoryModule(db_service)
            modules['moderation'] = ModerationModule(db_service, config) if config.moderation.enabled else None
            modules['analytics'] = AnalyticsModule(modules['analytics_service'])
            modules['behavior'] = BehaviorModule(db_service, modules['ai']) if modules['ai'] else None
            modules['stickers'] = StickersModule(db_service)
            modules['crypto'] = CryptoModule(modules['crypto_service']) if modules['crypto_service'] else None
            modules['charts'] = ChartsModule(db_service)
            
            print("⚡ Инициализация триггеров...")
            if TriggersModule:
                modules['triggers'] = TriggersModule(db_service, config)
            
            print("🔒 Инициализация разрешений...")
            if PermissionsModule:
                modules['permissions'] = PermissionsModule(config)
            
            # Отложенная загрузка
            print("📥 Загрузка триггеров и разрешений...")
            if modules['triggers']:
                await modules['triggers'].initialize()
            if modules['permissions']:
                await modules['permissions'].initialize()
            
            active_modules = sum(1 for m in modules.values() if m is not None and m != config and m != bot and m != db_service)
            print(f"  💀 Активных модулей: {active_modules}")
        
        else:
            print("⚠️ Базовый режим - модули недоступны")
        
        # ИСПРАВЛЕННАЯ РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
        print("🎛️ Регистрация ГРУБЫХ обработчиков...")
        register_all_handlers(dp, modules)
        print("  ✅ Обработчики зарегистрированы")
        
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
            startup_message = (
                "💀 **ГРУБЫЙ БОТ v3.0 ЗАПУЩЕН!**\n\n"
                f"**Бот:** @{bot_info.username}\n"
                f"**Режим:** МАКСИМАЛЬНО ГРУБЫЙ\n"
                f"**Разрешенных чатов:** {len(config.bot.allowed_chat_ids) if config.bot.allowed_chat_ids else 'Все'}\n\n"
                "**🔥 ОСОБЕННОСТИ:**\n"
                "• Логирование всех сообщений\n"
                "• Ответ только на обращения\n"
                "• Ответ только на команды\n"
                "• Ответ только на реплеи к боту\n"
                "• Редкая самостоятельная активность\n"
                "• Работа только в разрешенных чатах\n\n"
                "**ГОТОВ К РАБОТЕ!**"
            )
            
            for admin_id in config.bot.admin_ids:
                try:
                    await bot.send_message(admin_id, startup_message)
                    print(f"  📤 Админ уведомлен: {admin_id}")
                except Exception as e:
                    print(f"  ⚠️ Не удалось уведомить {admin_id}: {e}")
        
        print("\n" + "=" * 50)
        print("💀 ГРУБЫЙ БОТ v3.0 УСПЕШНО ЗАПУЩЕН!")
        print("=" * 50)
        print("\n🔥 ОСОБЕННОСТИ ГРУБОГО РЕЖИМА:")
        print("  • Логирование ВСЕХ сообщений чата")
        print("  • Ответ ТОЛЬКО при обращении к боту") 
        print("  • Ответ ТОЛЬКО на команды")
        print("  • Ответ ТОЛЬКО на реплеи к боту")
        print("  • Очень редкая самостоятельная активность")
        print("  • Жесткие ограничения по чатам")
        
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
        input("\nНажми Enter для выхода...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏸️ Остановка по запросу")
    except Exception as e:
        print(f"\n💥 Ошибка: {e}")
        input("Нажми Enter для выхода...")