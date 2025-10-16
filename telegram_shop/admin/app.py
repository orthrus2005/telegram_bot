from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import os
import sys
from datetime import datetime, timedelta
import json

# Добавляем путь к корневой папке проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ADMIN_ID, DATABASE_URL
from database.models import Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Замените на случайный ключ

# Настройка базы данных
db_path = DATABASE_URL.replace('sqlite+aiosqlite:///', '')
engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(bind=engine)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id)

# Фильтры для шаблонов
@app.template_filter('format_date')
def format_date(value, format='%d.%m.%Y'):
    """Фильтр для форматирования даты"""
    if not value:
        return "—"
    
    if isinstance(value, str):
        try:
            # Пробуем распарсить строку в datetime
            if 'T' in value:
                # Формат ISO с T
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                # Другие форматы
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        except (ValueError, AttributeError):
            # Если не получается распарсить, возвращаем как есть
            return value[:10]  # Первые 10 символов (YYYY-MM-DD)
    
    if isinstance(value, datetime):
        return value.strftime(format)
    
    return str(value)

@app.template_filter('format_datetime')
def format_datetime(value, format='%d.%m.%Y %H:%M'):
    """Фильтр для форматирования даты и времени"""
    return format_date(value, format)

# Простая аутентификация - только ADMIN_ID из config.py
def authenticate_admin(telegram_id):
    return str(telegram_id) == str(ADMIN_ID)

# Маршруты
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        telegram_id = request.form.get('telegram_id')
        if authenticate_admin(telegram_id):
            user = AdminUser(telegram_id)
            login_user(user)
            return redirect(url_for('orders'))
        else:
            flash('❌ Неверный ID администратора', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    session = SessionLocal()
    try:
        # Получаем заказы с информацией о пользователях
        orders_data = session.execute(text("""
            SELECT o.*, u.username, u.first_name, u.last_name, u.telegram_id
            FROM orders o 
            LEFT JOIN users u ON o.user_id = u.id 
            ORDER BY o.created_at DESC
        """)).fetchall()
        
        # Получаем статистику
        stats = session.execute(text("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_orders,
                SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed_orders,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
                SUM(total_amount) as total_revenue
            FROM orders
            WHERE status != 'cancelled'
        """)).fetchone()
        
        return render_template('orders.html', 
                             orders=orders_data, 
                             stats=stats,
                             current_time=datetime.now())
    finally:
        session.close()

@app.route('/database')
@login_required
def database():
    session = SessionLocal()
    try:
        # Получаем статистику по всем таблицам
        tables = ['products', 'categories', 'brands', 'users', 'orders', 'order_items']
        stats = {}
        
        for table in tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            stats[table] = count
        
        # Последние 10 товаров
        products = session.execute(text("""
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            ORDER BY p.created_at DESC LIMIT 10
        """)).fetchall()
        
        return render_template('database.html', stats=stats, products=products)
    finally:
        session.close()

@app.route('/products')
@login_required
def products():
    session = SessionLocal()
    try:
        # Получаем все товары с информацией о категориях и брендах
        products = session.execute(text("""
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            ORDER BY p.name
        """)).fetchall()
        
        categories = session.execute(text("SELECT * FROM categories WHERE is_active = 1")).fetchall()
        brands = session.execute(text("SELECT * FROM brands WHERE is_active = 1")).fetchall()
        
        return render_template('products.html', 
                             products=products, 
                             categories=categories, 
                             brands=brands)
    finally:
        session.close()

@app.route('/categories')
@login_required
def categories():
    session = SessionLocal()
    try:
        categories = session.execute(text("SELECT * FROM categories ORDER BY name")).fetchall()
        return render_template('categories.html', categories=categories)
    finally:
        session.close()

@app.route('/brands')
@login_required
def brands():
    session = SessionLocal()
    try:
        brands = session.execute(text("SELECT * FROM brands ORDER BY name")).fetchall()
        return render_template('brands.html', brands=brands)
    finally:
        session.close()

# API endpoints
@app.route('/api/update_order_status', methods=['POST'])
@login_required
def update_order_status():
    data = request.json
    order_id = data.get('order_id')
    new_status = data.get('status')
    
    session = SessionLocal()
    try:
        # Обновляем статус заказа
        session.execute(
            text("UPDATE orders SET status = :status WHERE id = :id"),
            {"status": new_status, "id": order_id}
        )
        
        # Если статус "completed" или "cancelled", обновляем количество товаров
        if new_status in ['completed', 'cancelled']:
            order_items = session.execute(
                text("SELECT product_id, quantity FROM order_items WHERE order_id = :order_id"),
                {"order_id": order_id}
            ).fetchall()
            
            for item in order_items:
                if new_status == 'completed':
                    # Списание товара
                    session.execute(
                        text("""
                            UPDATE products 
                            SET quantity = quantity - :quantity,
                                reserved_quantity = reserved_quantity - :quantity
                            WHERE id = :product_id
                        """),
                        {"quantity": item.quantity, "product_id": item.product_id}
                    )
                elif new_status == 'cancelled':
                    # Возврат товара
                    session.execute(
                        text("""
                            UPDATE products 
                            SET reserved_quantity = reserved_quantity - :quantity
                            WHERE id = :product_id
                        """),
                        {"quantity": item.quantity, "product_id": item.product_id}
                    )
        
        session.commit()
        return jsonify({'success': True, 'message': 'Статус заказа обновлен'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@app.route('/api/add_product', methods=['POST'])
@login_required
def add_product():
    data = request.json
    session = SessionLocal()
    try:
        session.execute(
            text("""
                INSERT INTO products (name, description, price, quantity, category_id, brand_id, is_active)
                VALUES (:name, :description, :price, :quantity, :category_id, :brand_id, 1)
            """),
            {
                "name": data['name'],
                "description": data['description'],
                "price": float(data['price']),
                "quantity": int(data['quantity']),
                "category_id": int(data['category_id']),
                "brand_id": int(data['brand_id'])
            }
        )
        session.commit()
        return jsonify({'success': True, 'message': 'Товар добавлен'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@app.route('/api/update_product', methods=['POST'])
@login_required
def update_product():
    data = request.json
    session = SessionLocal()
    try:
        session.execute(
            text("""
                UPDATE products 
                SET name = :name, description = :description, price = :price, 
                    quantity = :quantity, category_id = :category_id, brand_id = :brand_id,
                    is_active = :is_active
                WHERE id = :id
            """),
            {
                "id": int(data['id']),
                "name": data['name'],
                "description": data['description'],
                "price": float(data['price']),
                "quantity": int(data['quantity']),
                "category_id": int(data['category_id']),
                "brand_id": int(data['brand_id']),
                "is_active": 1 if data.get('is_active', True) else 0
            }
        )
        session.commit()
        return jsonify({'success': True, 'message': 'Товар обновлен'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@app.route('/api/delete_product', methods=['POST'])
@login_required
def delete_product():
    data = request.json
    session = SessionLocal()
    try:
        session.execute(
            text("DELETE FROM products WHERE id = :id"),
            {"id": int(data['id'])}
        )
        session.commit()
        return jsonify({'success': True, 'message': 'Товар удален'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@app.route('/api/add_category', methods=['POST'])
@login_required
def add_category():
    data = request.json
    session = SessionLocal()
    try:
        session.execute(
            text("INSERT INTO categories (name, description, is_active) VALUES (:name, :description, 1)"),
            {"name": data['name'], "description": data.get('description', '')}
        )
        session.commit()
        return jsonify({'success': True, 'message': 'Категория добавлена'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@app.route('/api/update_category', methods=['POST'])
@login_required
def update_category():
    data = request.json
    session = SessionLocal()
    try:
        session.execute(
            text("UPDATE categories SET name = :name, description = :description WHERE id = :id"),
            {"id": int(data['id']), "name": data['name'], "description": data.get('description', '')}
        )
        session.commit()
        return jsonify({'success': True, 'message': 'Категория обновлена'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@app.route('/api/delete_category', methods=['POST'])
@login_required
def delete_category():
    data = request.json
    session = SessionLocal()
    try:
        session.execute(
            text("DELETE FROM categories WHERE id = :id"),
            {"id": int(data['id'])}
        )
        session.commit()
        return jsonify({'success': True, 'message': 'Категория удалена'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@app.route('/api/add_brand', methods=['POST'])
@login_required
def add_brand():
    data = request.json
    session = SessionLocal()
    try:
        session.execute(
            text("INSERT INTO brands (name, description, is_active) VALUES (:name, :description, 1)"),
            {"name": data['name'], "description": data.get('description', '')}
        )
        session.commit()
        return jsonify({'success': True, 'message': 'Бренд добавлен'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@app.route('/api/update_brand', methods=['POST'])
@login_required
def update_brand():
    data = request.json
    session = SessionLocal()
    try:
        session.execute(
            text("UPDATE brands SET name = :name, description = :description WHERE id = :id"),
            {"id": int(data['id']), "name": data['name'], "description": data.get('description', '')}
        )
        session.commit()
        return jsonify({'success': True, 'message': 'Бренд обновлен'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@app.route('/api/delete_brand', methods=['POST'])
@login_required
def delete_brand():
    data = request.json
    session = SessionLocal()
    try:
        session.execute(
            text("DELETE FROM brands WHERE id = :id"),
            {"id": int(data['id'])}
        )
        session.commit()
        return jsonify({'success': True, 'message': 'Бренд удален'})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

# 🆕 ИСПРАВЛЕННЫЙ ОТЛАДОЧНЫЙ МАРШРУТ
@app.route('/api/debug_products')
@login_required
def debug_products():
    """Отладочная информация о товарах"""
    session = SessionLocal()
    try:
        # Получаем все товары с полной информацией
        products_result = session.execute(text("""
            SELECT p.*, c.name as category_name, b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            ORDER BY p.category_id, p.brand_id
        """)).fetchall()
        
        # Группируем по категориям и брендам для отладки
        categories_result = session.execute(text("SELECT * FROM categories")).fetchall()
        brands_result = session.execute(text("SELECT * FROM brands")).fetchall()
        
        # Преобразуем в словари
        products = []
        for product in products_result:
            products.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'quantity': product.quantity,
                'category_id': product.category_id,
                'brand_id': product.brand_id,
                'is_active': product.is_active,
                'category_name': product.category_name,
                'brand_name': product.brand_name
            })
        
        categories = []
        for category in categories_result:
            categories.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'is_active': category.is_active
            })
            
        brands = []
        for brand in brands_result:
            brands.append({
                'id': brand.id,
                'name': brand.name,
                'description': brand.description,
                'is_active': brand.is_active
            })
        
        debug_info = {
            'total_products': len(products),
            'categories': categories,
            'brands': brands,
            'products_by_category': {},
            'products_by_brand': {},
            'all_products': products
        }
        
        for category in categories:
            category_products = [p for p in products if p['category_id'] == category['id']]
            debug_info['products_by_category'][category['name']] = {
                'count': len(category_products),
                'products': [{'id': p['id'], 'name': p['name'], 'brand': p['brand_name'], 'quantity': p['quantity']} for p in category_products]
            }
            
        for brand in brands:
            brand_products = [p for p in products if p['brand_id'] == brand['id']]
            debug_info['products_by_brand'][brand['name']] = {
                'count': len(brand_products),
                'products': [{'id': p['id'], 'name': p['name'], 'category': p['category_name'], 'quantity': p['quantity']} for p in brand_products]
            }
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)