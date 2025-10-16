#!/usr/bin/env python3
"""
Сервер админ-панели для Telegram магазина
Запуск: python admin_server.py
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from admin.app import app
from config import ADMIN_HOST, ADMIN_PORT, ADMIN_SECRET_KEY

def main():
    """Запуск сервера админ-панели"""
    print("🚀 Запуск админ-панели...")
    print(f"📊 Админ-панель доступна по адресу: http://{ADMIN_HOST}:{ADMIN_PORT}")
    print(f"🔐 ADMIN_ID из .env: {os.getenv('ADMIN_ID')}")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    # Устанавливаем секретный ключ из конфига
    app.secret_key = ADMIN_SECRET_KEY
    
    try:
        app.run(
            host=ADMIN_HOST,
            port=ADMIN_PORT,
            debug=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Админ-панель остановлена")
    except Exception as e:
        print(f"❌ Ошибка при запуске админ-панели: {e}")

if __name__ == '__main__':
    main()