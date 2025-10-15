from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="🛍️ Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
        [InlineKeyboardButton(text="📞 Связаться с продавцом", callback_data="contact_seller")],
        [InlineKeyboardButton(text="ℹ️ О магазине", callback_data="about")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_to_main_keyboard():
    """Кнопка возврата в главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 На главную", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)