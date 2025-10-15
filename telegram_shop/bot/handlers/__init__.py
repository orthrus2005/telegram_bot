from .start import router as start_router
from .catalog import router as catalog_router
from .cart import router as cart_router
from .order import router as order_router
from .admin import router as admin_router

__all__ = [
    'start_router',
    'catalog_router', 
    'cart_router',
    'order_router',
    'admin_router'
]