from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from database.models import CartItem
from database.repository import UserRepository
from bot.keyboards.main_menu import get_main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Обработчик команды /start"""
    # Создаем или получаем пользователя
    user = await UserRepository.get_or_create_user(
        session=session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # ОЧИСТКА КОРЗИНЫ ПРИ КАЖДОМ СТАРТЕ
    await session.execute(delete(CartItem).where(CartItem.user_id == user.id))
    await session.commit()
    
    await message.answer(
        "🏪 Добро пожаловать в наш магазин!\n\n"
        "Здесь вы можете приобрести качественные товары с быстрой доставкой.\n"
        "Выберите действие в меню ниже:",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🏪 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "about")
async def about_shop(callback: CallbackQuery):
    """Информация о магазине"""
    await callback.message.edit_text(
        "🏪 О нашем магазине\n\n"
        "• Быстрая доставка\n"
        "• Качественные товары\n"
        "• Поддержка 24/7\n"
        "• Удобная оплата\n\n"
        "По всем вопросам обращайтесь к нашему менеджеру!",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "contact_seller")
async def contact_seller(callback: CallbackQuery):
    """Связь с продавцом"""
    await callback.message.edit_text(
        "📞 Связь с продавцом\n\n"
        "Для связи с менеджером:\n"
        "• Напишите нам в личные сообщения\n"
        "• Или позвоните по номеру: +7 (XXX) XXX-XX-XX\n\n"
        "Мы всегда рады помочь!",
        reply_markup=get_main_menu()
    )