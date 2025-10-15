from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import User, Product, Category, Brand, CartItem

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
        # Проверяем есть ли уже товар в корзине
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
        result = await session.scalars(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .join(CartItem.product)
        )
        return result.all()