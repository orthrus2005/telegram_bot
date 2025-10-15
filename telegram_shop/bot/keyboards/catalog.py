from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_categories_keyboard(categories):
    """Клавиатура категорий"""
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📁 {category.name}", 
                callback_data=f"category_{category.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 На главную", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_brands_keyboard(brands, back_to="catalog"):
    """Клавиатура брендов"""
    keyboard = []
    for brand in brands:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🏷️ {brand.name}", 
                callback_data=f"brand_{brand.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_products_keyboard(products, back_to="brands"):
    """Клавиатура товаров"""
    keyboard = []
    for product in products:
        status_icon = "✅" if product.quantity > 0 else "❌"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_icon} {product.name} - {product.price}₽", 
                callback_data=f"product_{product.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_product_detail_keyboard(product_id, back_to="products"):
    """Клавиатура для детальной страницы товара"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_to_cart_{product_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)