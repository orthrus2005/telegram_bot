from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cart_keyboard(cart_items):
    """Клавиатура корзины"""
    keyboard = []
    
    for item in cart_items:
        keyboard.extend([
            [
                InlineKeyboardButton(text="➖", callback_data=f"decrease_{item.id}"),
                InlineKeyboardButton(text=f"{item.product.name} ({item.quantity} шт.)", callback_data=f"item_{item.id}"),
                InlineKeyboardButton(text="➕", callback_data=f"increase_{item.id}")
            ],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"remove_{item.id}")]
        ])
    
    if cart_items:
        keyboard.append([InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")])
    
    # Кнопка для продолжения покупок
    keyboard.append([InlineKeyboardButton(text="🛍️ Продолжить покупки", callback_data="catalog")])
    keyboard.append([InlineKeyboardButton(text="🔙 На главную", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_checkout_confirm_keyboard():
    """Подтверждение оформления заказа"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton(text="✏️ Изменить данные", callback_data="edit_checkout")],
        [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_order")],
        [InlineKeyboardButton(text="🔙 В корзину", callback_data="cart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_delivery_method_keyboard():
    """Выбор способа доставки - только самовывоз"""
    keyboard = [
        [InlineKeyboardButton(text="🏢 3-е общежитие ВГТУ", callback_data="pickup_vgtu")],
        [InlineKeyboardButton(text="🏠 ул.Терешковой 16к1", callback_data="pickup_tereshkovoy")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="checkout")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_payment_method_keyboard():
    """Выбор способа оплаты - наличные и карта (недоступно)"""
    keyboard = [
        [InlineKeyboardButton(text="💵 Наличные при получении", callback_data="payment_cash")],
        [InlineKeyboardButton(text="💳 Карта (скоро)", callback_data="payment_card_disabled")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="checkout_delivery")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_dates_keyboard():
    """Клавиатура с датами на текущей неделе (без выходных)"""
    from datetime import datetime, timedelta
    
    keyboard = []
    today = datetime.now()
    
    # Добавляем даты на 7 дней вперед, пропуская выходные
    for i in range(7):
        current_date = today + timedelta(days=i)
        # Пропускаем субботу (5) и воскресенье (6)
        if current_date.weekday() not in [5, 6]:
            date_str = current_date.strftime("%d.%m.%Y")
            weekday = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][current_date.weekday()]
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{weekday} {date_str}",
                    callback_data=f"date_{date_str}"
                )
            ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="checkout_payment")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_to_checkout_keyboard():
    """Кнопка возврата к оформлению заказа"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Вернуться к оформлению", callback_data="checkout")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)