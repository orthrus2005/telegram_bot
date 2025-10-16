from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.middlewares.database import DatabaseMiddleware
import config
from database.engine import init_db

# Импортируем роутеры напрямую
from bot.handlers.start import router as start_router
from bot.handlers.catalog import router as catalog_router
from bot.handlers.cart import router as cart_router
from bot.handlers.order import router as order_router
from bot.handlers.admin import router as admin_router

async def setup_bot():
    """Настройка и запуск бота"""
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Добавляем middleware для работы с базой данных
    dp.update.middleware(DatabaseMiddleware())
    
    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(catalog_router)
    dp.include_router(cart_router)
    dp.include_router(order_router)
    dp.include_router(admin_router)
    
    return bot, dp

async def start_bot():
    """Запуск бота"""
    await init_db()
    bot, dp = await setup_bot()
    
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)