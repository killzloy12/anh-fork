#!/usr/bin/env python3
"""
Enhanced Telegram Bot v2.0 - Windows Compatible Installer
Автоматическая установка и настройка бота (совместимо с Windows)
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def run_command(command):
    """Выполнение команды"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def main():
    print("Enhanced Telegram Bot v2.0 - Установка")
    print("=" * 50)
    
    # Проверка Python версии
    if sys.version_info < (3, 8):
        print("ОШИБКА: Требуется Python 3.8 или выше!")
        print(f"Текущая версия: {sys.version}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Создание виртуального окружения
    print("\\nСоздание виртуального окружения...")
    venv_command = "python -m venv venv"
    if platform.system() != "Windows":
        venv_command = "python3 -m venv venv"
    
    success, output = run_command(venv_command)
    if not success:
        print(f"ОШИБКА создания venv: {output}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    print("Виртуальное окружение создано")
    
    # Определяем команды активации
    if platform.system() == "Windows":
        pip_cmd = "venv\\\\Scripts\\\\pip.exe"
        activate_cmd = "venv\\\\Scripts\\\\activate"
    else:
        pip_cmd = "venv/bin/pip"
        activate_cmd = "source venv/bin/activate"
    
    # Обновление pip
    print("\\nОбновление pip...")
    success, output = run_command(f"{pip_cmd} install --upgrade pip")
    if not success:
        print(f"Предупреждение: {output}")
    
    # Установка зависимостей
    print("\\nУстановка зависимостей...")
    success, output = run_command(f"{pip_cmd} install -r requirements.txt")
    if not success:
        print(f"ОШИБКА установки зависимостей: {output}")
        print("\\nПопробуйте установить зависимости по одной:")
        print("pip install aiogram aiosqlite python-dotenv requests matplotlib")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    print("Зависимости установлены")
    
    # Создание .env файла
    print("\\nНастройка конфигурации...")
    if not Path('.env').exists():
        if Path('.env.example').exists():
            import shutil
            shutil.copy('.env.example', '.env')
            print("Файл .env создан из примера")
        else:
            print("ВНИМАНИЕ: Файл .env.example не найден")
    else:
        print("Файл .env уже существует")
    
    # Создание директорий
    print("\\nСоздание директорий...")
    directories = [
        'data', 'data/logs', 'data/models', 'data/charts', 
        'data/exports', 'data/backups', 'app', 'app/services', 
        'app/modules', 'app/handlers'
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("Директории созданы")
    
    # Создание пустых __init__.py файлов
    print("\\nСоздание файлов инициализации...")
    init_files = [
        'app/__init__.py',
        'app/services/__init__.py', 
        'app/modules/__init__.py'
    ]
    
    for init_file in init_files:
        init_path = Path(init_file)
        if not init_path.exists():
            init_path.touch()
            print(f"Создан {init_file}")
    
    print("\\n" + "=" * 50)
    print("УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 50)
    
    print("\\nСледующие шаги:")
    print("1. Отредактируйте файл .env своими токенами:")
    print("   - BOT_TOKEN=your_telegram_bot_token")
    print("   - ADMIN_IDS=your_telegram_id")
    print("   - OPENAI_API_KEY=your_openai_key (опционально)")
    
    print("\\n2. Запустите бота:")
    if platform.system() == "Windows":
        print(f"   {activate_cmd}")
        print("   python main.py")
    else:
        print(f"   {activate_cmd}")
        print("   python3 main.py")
    
    print("\\n3. Или без виртуального окружения:")
    if platform.system() == "Windows":
        print("   python main.py")
    else:
        print("   python3 main.py")
    
    print("\\nEnhanced Telegram Bot v2.0 готов к запуску!")
    print("\\nЕсли возникнут проблемы:")
    print("- Проверьте настройки в .env файле")
    print("- Убедитесь что все зависимости установлены")
    print("- Проверьте логи в data/logs/bot.log")
    
    input("\\nНажмите Enter для выхода...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\nОстановка по запросу пользователя")
    except Exception as e:
        print(f"\\nКритическая ошибка: {e}")
        input("Нажмите Enter для выхода...")