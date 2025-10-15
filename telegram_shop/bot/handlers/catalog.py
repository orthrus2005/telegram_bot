from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Category, Brand, Product
from utils.states import OrderStates
from bot.keyboards.catalog import (
    get_categories_keyboard, get_brands_keyboard, 
    get_products_keyboard, get_product_detail_keyboard
)
from bot.keyboards.main_menu import get_main_menu
from utils.helpers import get_product_status_text

router = Router()

@router.callback_query(F.data == "catalog")
async def show_categories(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать категории"""
    # Получаем активные категории
    result = await session.scalars(
        select(Category).where(Category.is_active == True)
    )
    categories = result.all()
    
    if not categories:
        await callback.message.edit_text(
            "📦 Категории временно недоступны",
            reply_markup=get_main_menu()
        )
        return
    
    await callback.message.edit_text(
        "📁 Выберите категорию:",
        reply_markup=get_categories_keyboard(categories)
    )
    await state.set_state(OrderStates.catalog)

@router.callback_query(F.data.startswith("category_"))
async def show_brands(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать бренды по категории"""
    category_id = int(callback.data.split("_")[1])
    
    # Получаем бренды для этой категории
    result = await session.scalars(
        select(Brand)
        .join(Brand.products)
        .where(Product.category_id == category_id)
        .where(Brand.is_active == True)
        .distinct()
    )
    brands = result.all()
    
    if not brands:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🏷️ Выберите производителя:",
        reply_markup=get_brands_keyboard(brands, f"category_{category_id}")
    )
    await state.set_state(OrderStates.liquid_brands)

@router.callback_query(F.data.startswith("brand_"))
async def show_products(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать товары бренда"""
    brand_id = int(callback.data.split("_")[1])
    
    # Получаем товары бренда
    result = await session.scalars(
        select(Product)
        .where(Product.brand_id == brand_id)
        .where(Product.is_active == True)
        .order_by(Product.name)
    )
    products = result.all()
    
    if not products:
        await callback.answer("У этого производителя пока нет товаров", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🛍️ Выберите товар:",
        reply_markup=get_products_keyboard(products, f"brand_{brand_id}")
    )
    await state.set_state(OrderStates.liquid_products)

@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery, session: AsyncSession):
    """Показать детали товара"""
    product_id = int(callback.data.split("_")[1])
    
    # Используем eager loading чтобы избежать проблем с lazy loading
    stmt = select(Product).options(
        selectinload(Product.brand),
        selectinload(Product.category)
    ).where(Product.id == product_id)
    
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    status_text = await get_product_status_text(product)
    
    product_text = (
        f"🛍️ {product.name}\n"
        f"🏷️ {product.brand.name}\n"
        f"📁 {product.category.name}\n\n"
        f"{product.description}\n\n"
        f"💵 Цена: {product.price}₽\n"
        f"📦 {status_text}"
    )
    
    await callback.message.edit_text(
        product_text,
        reply_markup=get_product_detail_keyboard(product_id, f"brand_{product.brand.id}")
    )

@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery, session: AsyncSession):
    """Возврат к списку товаров"""
    await show_categories(callback, session, None)

@router.callback_query(F.data == "back_to_brands")
async def back_to_brands(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Возврат к списку брендов"""
    await show_categories(callback, session, state)

@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Возврат в каталог"""
    await show_categories(callback, session, state)