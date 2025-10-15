import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import AsyncSessionLocal
from database.models import Category, Brand, Product

async def add_test_data():
    async with AsyncSessionLocal() as session:
        print("🔄 Добавляем тестовые данные...")
        
        # Добавляем категории
        categories = [
            Category(name="Жидкости", description="Электронные жидкости для вейпа"),
            Category(name="Расходники", description="Картриджи, испарители, аккумуляторы"),
            Category(name="Устройства", description="Электронные сигареты и pod-системы")
        ]
        session.add_all(categories)
        await session.commit()
        print("✅ Категории добавлены")
        
        # Добавляем бренды
        brands = [
            Brand(name="HQD", description="Популярные одноразовые электронные сигареты"),
            Brand(name="Puff Bar", description="Стильные одноразовые устройства"),
            Brand(name="Vaporesso", description="Качественные расходные материалы"),
            Brand(name="Elf Bar", description="Лидер рынка одноразок")
        ]
        session.add_all(brands)
        await session.commit()
        print("✅ Бренды добавлены")
        
        # Добавляем товары
        products = [
            # Жидкости
            Product(
                name="HQD Cuvie Plus 1200",
                description="Одноразовая электронная сигарета, 1200 затяжек\nВкус: Мята с ментолом\nКрепость: 20mg",
                price=1200,
                quantity=10,
                category_id=1,
                brand_id=1
            ),
            Product(
                name="Puff Bar Plus 800", 
                description="Стильная одноразка, 800 затяжек\nВкус: Клубника-банан\nКрепость: 15mg",
                price=900,
                quantity=5,
                category_id=1, 
                brand_id=2
            ),
            Product(
                name="Elf Bar BC5000",
                description="Легендарная одноразка, 5000 затяжек\nВкус: Голубика-малина\nКрепость: 20mg",
                price=2500,
                quantity=3,
                category_id=1,
                brand_id=4
            ),
            
            # Расходники
            Product(
                name="Испаритель Vaporesso",
                description="Сменный испаритель для pod-систем\nСопротивление: 0.8 Ом\nСовместимость: XROS серия",
                price=300,
                quantity=20,
                category_id=2,
                brand_id=3
            ),
            Product(
                name="Картриджи HQD",
                description="Сменные картриджи для HQD\nОбъем: 2ml\nКрепость: 20mg",
                price=400,
                quantity=15,
                category_id=2,
                brand_id=1
            ),
            
            # Устройства
            Product(
                name="Vaporesso XROS 4",
                description="Многоразовая pod-система\nАккумулятор: 1000mAh\nТип зарядки: USB-C",
                price=3500,
                quantity=8,
                category_id=3,
                brand_id=3
            )
        ]
        session.add_all(products)
        
        await session.commit()
        print("✅ Товары добавлены")
        print("🎉 Все тестовые данные успешно добавлены в базу!")

if __name__ == "__main__":
    asyncio.run(add_test_data())