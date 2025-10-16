import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL")

# 🆕 ДОБАВЛЕНО: Настройки админ-панели
ADMIN_HOST = os.getenv("ADMIN_HOST", "0.0.0.0")
ADMIN_PORT = int(os.getenv("ADMIN_PORT", "5000"))
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "your-secret-key-change-in-production")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле")

if not ADMIN_ID:
    print("⚠️  ADMIN_ID не установлен. Админ-панель будет недоступна.")