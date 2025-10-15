from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order, OrderItem, User
from database.repository import UserRepository, CartRepository
from utils.states import OrderStates
from bot.keyboards.cart import (
    get_checkout_confirm_keyboard, 
    get_delivery_method_keyboard, 
    get_payment_method_keyboard,
    get_dates_keyboard,
    get_back_to_checkout_keyboard
)
from bot.keyboards.main_menu import get_main_menu

router = Router()

@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Начало оформления заказа - сразу выбор пункта выдачи"""
    await callback.message.edit_text(
        "🚚 Выберите пункт выдачи:\n\n"
        "🏢 3-е общежитие ВГТУ\n"
        "🏠 ул.Терешковой 16к1",
        reply_markup=get_delivery_method_keyboard()
    )
    await state.set_state(OrderStates.checkout_delivery_method)

@router.callback_query(F.data.startswith("pickup_"))
async def process_delivery_method(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора пункта выдачи"""
    if "vgtu" in callback.data:
        delivery_address = "3-е общежитие ВГТУ"
    else:
        delivery_address = "ул.Терешковой 16к1"
    
    await state.update_data(
        delivery_method="pickup",
        delivery_address=delivery_address,
        customer_name="Клиент"  # Автоматическое имя
    )
    
    await callback.message.edit_text(
        "📅 Выберите дату получения заказа (доступны только будние дни):",
        reply_markup=get_dates_keyboard()
    )
    await state.set_state(OrderStates.checkout_date)

@router.callback_query(F.data.startswith("date_"))
async def process_date(callback: CallbackQuery, state: FSMContext):
    """Обработка даты доставки"""
    delivery_date = callback.data.split("_")[1]
    await state.update_data(delivery_date=delivery_date)
    
    # Автоматически устанавливаем время
    await state.update_data(delivery_time="16:00-18:00")
    
    await callback.message.edit_text(
        "💳 Выберите способ оплаты:",
        reply_markup=get_payment_method_keyboard()
    )
    await state.set_state(OrderStates.checkout_payment)

@router.callback_query(F.data.startswith("payment_"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    """Обработка способа оплаты"""
    if "disabled" in callback.data:
        await callback.answer("❌ Оплата картой временно недоступна", show_alert=True)
        return
    
    payment_method = "cash" if "cash" in callback.data else "card"
    await state.update_data(payment_method=payment_method)
    
    # Автоматически устанавливаем примечание
    await state.update_data(notes="")
    
    # Показываем подтверждение заказа
    await show_order_confirmation(callback, state)

@router.callback_query(F.data == "edit_checkout")
async def edit_checkout(callback: CallbackQuery, state: FSMContext):
    """Редактирование данных заказа"""
    await start_checkout(callback, state)

@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отмена заказа"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Заказ отменен",
        reply_markup=get_main_menu()
    )

async def show_order_confirmation(callback: CallbackQuery, state: FSMContext, session: AsyncSession = None):
    """Показать подтверждение заказа с деталями"""
    order_data = await state.get_data()
    
    if session:
        user = await UserRepository.get_or_create_user(
            session=session,
            telegram_id=callback.from_user.id
        )
        cart_items = await CartRepository.get_cart_items(session, user.id)
        
        # Рассчитываем итоговую сумму
        total_amount = sum(item.product.price * item.quantity for item in cart_items)
        
        # Формируем текст заказа для подтверждения
        order_text = (
            "📋 ПОДТВЕРЖДЕНИЕ ЗАКАЗА\n\n"
            "📍 Данные доставки:\n"
            f"   🚗 Самовывоз: {order_data['delivery_address']}\n"
            f"   📅 Дата: {order_data['delivery_date']}\n"
            f"   ⏰ Время: {order_data['delivery_time']}\n"
            f"   💳 Оплата: {'Наличные при получении' if order_data['payment_method'] == 'cash' else 'Карта'}\n\n"
        )
        
        order_text += "🛒 СОСТАВ ЗАКАЗА:\n"
        for item in cart_items:
            item_total = item.product.price * item.quantity
            order_text += f"   • {item.product.name}\n"
            order_text += f"     {item.quantity} шт. × {item.product.price}₽ = {item_total}₽\n"
        
        order_text += f"\n💵 ИТОГО: {total_amount}₽"
        
        await callback.message.edit_text(
            order_text,
            reply_markup=get_checkout_confirm_keyboard()
        )
    else:
        # Если сессии нет, показываем базовую информацию
        order_text = (
            "📋 Подтверждение заказа:\n\n"
            f"🚗 Самовывоз: {order_data['delivery_address']}\n"
            f"📅 Дата: {order_data['delivery_date']}\n"
            f"⏰ Время: {order_data['delivery_time']}\n"
            f"💳 Оплата: {'Наличные при получении' if order_data['payment_method'] == 'cash' else 'Карта'}\n\n"
            "Для полной информации добавьте товары в корзину"
        )
        
        await callback.message.edit_text(
            order_text,
            reply_markup=get_checkout_confirm_keyboard()
        )

@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтверждение и создание заказа"""
    try:
        order_data = await state.get_data()
        
        user = await UserRepository.get_or_create_user(
            session=session,
            telegram_id=callback.from_user.id
        )
        cart_items = await CartRepository.get_cart_items(session, user.id)
        
        if not cart_items:
            await callback.answer("❌ Корзина пуста!", show_alert=True)
            return
        
        # Рассчитываем итоговую сумму
        total_amount = sum(item.product.price * item.quantity for item in cart_items)
        
        # Создаем заказ
        order = Order(
            user_id=user.id,
            total_amount=total_amount,
            customer_name=order_data['customer_name'],
            delivery_method=order_data['delivery_method'],
            delivery_address=order_data['delivery_address'],
            delivery_date=order_data['delivery_date'],
            delivery_time=order_data['delivery_time'],
            payment_method=order_data['payment_method'],
            notes=order_data.get('notes', '')
        )
        session.add(order)
        await session.commit()
        
        # Добавляем товары в заказ
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product.id,
                product_name=cart_item.product.name,
                product_price=cart_item.product.price,
                quantity=cart_item.quantity
            )
            session.add(order_item)
        
        # Очищаем корзину
        for cart_item in cart_items:
            await session.delete(cart_item)
        
        await session.commit()
        await state.clear()
        
        await callback.message.edit_text(
            "✅ Заказ успешно оформлен!\n\n"
            f"📦 Номер вашего заказа: #{order.id}\n"
            f"📍 Пункт выдачи: {order_data['delivery_address']}\n"
            f"📅 Дата: {order_data['delivery_date']}\n"
            f"⏰ Время: {order_data['delivery_time']}\n"
            f"💳 Оплата: {'Наличные при получении' if order_data['payment_method'] == 'cash' else 'Карта'}\n\n"
            "📞 С вами свяжется наш менеджер для подтверждения.\n\n"
            "Спасибо за покупку! 🛍️",
            reply_markup=get_main_menu()
        )
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ Произошла ошибка при оформлении заказа. Попробуйте позже.",
            reply_markup=get_main_menu()
        )

# Обработчики для кнопок "Назад"
@router.callback_query(F.data == "checkout_delivery")
async def back_to_delivery(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору доставки"""
    await start_checkout(callback, state)

@router.callback_query(F.data == "checkout_payment")
async def back_to_payment(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору оплаты"""
    await callback.message.edit_text(
        "💳 Выберите способ оплаты:",
        reply_markup=get_payment_method_keyboard()
    )
    await state.set_state(OrderStates.checkout_payment)