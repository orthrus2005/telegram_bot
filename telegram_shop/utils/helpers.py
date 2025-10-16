from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Product

async def check_product_availability(session: AsyncSession, product_id: int, quantity: int = 1) -> bool:
    """Проверяет доступно ли достаточное количество товара"""
    product = await session.get(Product, product_id)
    return product and product.quantity >= quantity and product.is_active

async def get_product_status_text(product: Product) -> str:
    """Возвращает текст статуса товара"""
    if not product.is_active:
        return "❌ Не доступен"
    elif product.quantity == 0:
        return "📦 Закончился"
    elif product.quantity <= 5:
        return f"⚠️ Осталось мало ({product.quantity} шт)"
    else:
        return f"✅ В наличии ({product.quantity} шт)"

# 🆕 ИСПРАВЛЕННАЯ ФУНКЦИЯ (без reserved_quantity)
async def get_available_quantity(product: Product) -> int:
    """Возвращает доступное количество товара"""
    return max(0, product.quantity)