from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from database.models import CartItem
from database.repository import CartRepository, UserRepository
from bot.keyboards.cart import get_cart_keyboard
from bot.keyboards.main_menu import get_main_menu
from utils.helpers import check_product_availability

router = Router()

@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery, session: AsyncSession):
    """Показать корзину"""
    user = await UserRepository.get_or_create_user(
        session=session,
        telegram_id=callback.from_user.id
    )
    
    # Используем eager loading для корзины
    stmt = select(CartItem).options(
        selectinload(CartItem.product)
    ).where(CartItem.user_id == user.id)
    
    result = await session.execute(stmt)
    cart_items = result.scalars().all()
    
    if not cart_items:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста\n\n"
            "Добавьте товары из каталога!",
            reply_markup=get_main_menu()
        )
        return
    
    # Формируем текст корзины
    cart_text = "🛒 Ваша корзина:\n\n"
    total = 0
    
    for item in cart_items:
        item_total = item.product.price * item.quantity
        total += item_total
        status_icon = "✅" if item.product.quantity >= item.quantity else "⚠️"
        cart_text += f"{status_icon} {item.product.name}\n"
        cart_text += f"   {item.quantity} шт. x {item.product.price}₽ = {item_total}₽\n\n"
    
    cart_text += f"💵 Итого: {total}₽"
    
    await callback.message.edit_text(
        cart_text,
        reply_markup=get_cart_keyboard(cart_items)
    )

@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery, session: AsyncSession):
    """Добавить товар в корзину"""
    product_id = int(callback.data.split("_")[3])
    
    # Проверяем доступность товара
    is_available = await check_product_availability(session, product_id)
    if not is_available:
        await callback.answer("❌ Товар временно недоступен", show_alert=True)
        return
    
    user = await UserRepository.get_or_create_user(
        session=session,
        telegram_id=callback.from_user.id
    )
    
    # Добавляем в корзину
    await CartRepository.add_to_cart(session, user.id, product_id)
    
    await callback.answer("✅ Товар добавлен в корзину!")

@router.callback_query(F.data.startswith("increase_"))
async def increase_quantity(callback: CallbackQuery, session: AsyncSession):
    """Увеличить количество товара в корзине"""
    cart_item_id = int(callback.data.split("_")[1])
    
    # Находим товар в корзине
    cart_item = await session.get(CartItem, cart_item_id)
    if cart_item:
        cart_item.quantity += 1
        await session.commit()
        await callback.answer("✅ Количество увеличено")
    await show_cart(callback, session)

@router.callback_query(F.data.startswith("decrease_"))
async def decrease_quantity(callback: CallbackQuery, session: AsyncSession):
    """Уменьшить количество товара в корзине"""
    cart_item_id = int(callback.data.split("_")[1])
    
    # Находим товар в корзине
    cart_item = await session.get(CartItem, cart_item_id)
    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            await session.commit()
            await callback.answer("✅ Количество уменьшено")
        else:
            await callback.answer("❌ Нельзя уменьшить меньше 1", show_alert=True)
    await show_cart(callback, session)

@router.callback_query(F.data.startswith("remove_"))
async def remove_from_cart(callback: CallbackQuery, session: AsyncSession):
    """Удалить товар из корзины"""
    cart_item_id = int(callback.data.split("_")[1])
    
    # Удаляем товар из корзины
    await session.execute(delete(CartItem).where(CartItem.id == cart_item_id))
    await session.commit()
    
    await callback.answer("🗑️ Товар удален из корзины")
    await show_cart(callback, session)