from .db import db
from .user import User
from .product import Product
from .transaction import Transaction

def init_app(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
# Export all models
__all__ = ['db', 'BaseModel', 'User', 'product', 'Transaction', 'init_app']
