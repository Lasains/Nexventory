from app.extensions import db
from sqlalchemy import CheckConstraint


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    min_stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255), nullable=True)  # New field for image filename
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # DB-level safety net: prevents stock from going negative even if app logic has a bug.
    # This is the last line of defense after the SELECT FOR UPDATE guard in routes.
    __table_args__ = (
        CheckConstraint('stock >= 0', name='ck_product_stock_non_negative'),
    )

    @property
    def sku(self):
        cat_prefix = (self.category[:3] if self.category else 'GEN').upper()
        return f"SKU-{cat_prefix}-{self.id:04d}"

    def __repr__(self):
        return f'<Product {self.name}>'