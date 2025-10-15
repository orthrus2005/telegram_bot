from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    catalog = State()
    liquid_brands = State()
    liquid_products = State()
    consumables = State()
    cart = State()
    checkout_delivery_method = State()
    checkout_date = State()
    checkout_payment = State()

class AdminStates(StatesGroup):
    add_product = State()
    edit_product = State()
    add_category = State()
    add_brand = State()