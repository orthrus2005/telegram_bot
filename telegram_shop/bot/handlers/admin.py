from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

import config
from utils.states import AdminStates

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Панель администратора"""
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("❌ Доступ запрещен")
        return
    
    await message.answer(
        "👨‍💼 Панель администратора\n\n"
        "Доступные команды:\n"
        "/add_product - Добавить товар\n"
        "/add_category - Добавить категорию\n"
        "/add_brand - Добавить бренд\n"
        "/stats - Статистика"
    )

# Здесь будут другие обработчики для админки
# Мы их добавим позже