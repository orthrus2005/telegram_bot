from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload  # 🆕 ДОБАВИТЬ ЭТОТ ИМПОРТ
from database.models import Order, OrderItem, User, Product, CartItem
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
import config

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
        "💳 Выберите способ оплата:",
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

async def send_admin_notification(bot: Bot, order: Order, user: User, order_items_text: str):
    """Отправка уведомления администратору"""
    admin_message = (
        "🆕 НОВЫЙ ЗАКАЗ!\n\n"
        f"📦 Номер заказа: #{order.id}\n"
        f"👤 Клиент: {user.first_name or ''} {user.last_name or ''} (@{user.username or 'без username'})\n"
        f"📞 Telegram ID: {user.telegram_id}\n"
        f"💵 Сумма: {order.total_amount}₽\n"
        f"📍 Пункт выдачи: {order.delivery_address}\n"
        f"📅 Дата: {order.delivery_date}\n"
        f"⏰ Время: {order.delivery_time}\n"
        f"💳 Оплата: {'Наличные' if order.payment_method == 'cash' else 'Карта'}\n\n"
        f"🛒 Состав заказа:\n{order_items_text}\n\n"
        "⚡ Перейдите в админ-панель для управления заказом"
    )
    
    try:
        await bot.send_message(chat_id=config.ADMIN_ID, text=admin_message)
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления админу: {e}")

@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Подтверждение и создание заказа"""
    try:
        order_data = await state.get_data()
        
        user = await UserRepository.get_or_create_user(
            session=session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name
        )
        
        # Получаем cart_items с продуктами
        stmt = select(CartItem).options(
            selectinload(CartItem.product)
        ).where(CartItem.user_id == user.id)
        
        result = await session.execute(stmt)
        cart_items = result.scalars().all()
        
        if not cart_items:
            await callback.answer("❌ Корзина пуста!", show_alert=True)
            return
        
        # Рассчитываем итоговую сумму
        total_amount = sum(item.product.price * item.quantity for item in cart_items)
        
        # Создаем заказ (БЕЗ updated_at)
        order = Order(
            user_id=user.id,
            total_amount=total_amount,
            customer_name=order_data['customer_name'],
            delivery_method=order_data['delivery_method'],
            delivery_address=order_data['delivery_address'],
            delivery_date=order_data['delivery_date'],
            delivery_time=order_data['delivery_time'],
            payment_method=order_data['payment_method'],
            notes=order_data.get('notes', ''),
            status='pending'
        )
        session.add(order)
        await session.flush()  # Используем flush вместо commit чтобы получить ID
        
        # Формируем текст товаров для уведомления
        order_items_text = ""
        for cart_item in cart_items:
            item_total = cart_item.product.price * cart_item.quantity
            order_items_text += f"   • {cart_item.product.name}\n"
            order_items_text += f"     {cart_item.quantity} шт. × {cart_item.product.price}₽ = {item_total}₽\n"
            
            # Добавляем товары в заказ
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product.id,
                product_name=cart_item.product.name,
                product_price=cart_item.product.price,
                quantity=cart_item.quantity
            )
            session.add(order_item)
            
            # Обновляем количество товара
            product = await session.get(Product, cart_item.product.id)
            if product:
                product.quantity = max(0, product.quantity - cart_item.quantity)
        
        # Очищаем корзину
        for cart_item in cart_items:
            await session.delete(cart_item)
        
        await session.commit()  # Один коммит в конце
        
        await state.clear()
        
        # Отправляем уведомление администратору
        await send_admin_notification(bot, order, user, order_items_text)
        
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
        print(f"❌ Ошибка при создании заказа: {e}")
        await session.rollback()  # Откатываем изменения при ошибке
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