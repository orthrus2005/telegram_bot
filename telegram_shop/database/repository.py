from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload  # 🆕 ДОБАВИТЬ ЭТОТ ИМПОРТ
from database.models import User, Product, Category, Brand, CartItem, Order, OrderItem

class UserRepository:
    @staticmethod
    async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str = None,
                               first_name: str = None, last_name: str = None) -> User:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            await session.commit()
        return user

class ProductRepository:
    @staticmethod
    async def get_available_products(session: AsyncSession) -> list[Product]:
        result = await session.scalars(
            select(Product)
            .where(Product.is_active == True)
            .where(Product.quantity > 0)
        )
        return result.all()
    
    @staticmethod
    async def get_products_by_category(session: AsyncSession, category_id: int) -> list[Product]:
        result = await session.scalars(
            select(Product)
            .where(Product.category_id == category_id)
            .where(Product.is_active == True)
        )
        return result.all()
    
    @staticmethod
    async def update_product_quantity(session: AsyncSession, product_id: int, new_quantity: int):
        await session.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(quantity=new_quantity)
        )
        await session.commit()

class CartRepository:
    @staticmethod
    async def add_to_cart(session: AsyncSession, user_id: int, product_id: int, quantity: int = 1):
        existing_item = await session.scalar(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .where(CartItem.product_id == product_id)
        )
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            session.add(cart_item)
        
        await session.commit()

    @staticmethod
    async def get_cart_items(session: AsyncSession, user_id: int) -> list[CartItem]:
        from sqlalchemy.orm import selectinload
        
        stmt = select(CartItem).options(
            selectinload(CartItem.product)
        ).where(CartItem.user_id == user_id)
        
        result = await session.execute(stmt)
        return result.scalars().all()

class OrderRepository:
    @staticmethod
    async def get_orders(session: AsyncSession, status: str = None) -> list[Order]:
        query = select(Order).join(Order.user)
        if status:
            query = query.where(Order.status == status)
        result = await session.scalars(query.order_by(Order.created_at.desc()))
        return result.all()

    @staticmethod
    async def update_order_status(session: AsyncSession, order_id: int, new_status: str):
        order = await session.get(Order, order_id)
        if order:
            order.status = new_status
            await session.commit()