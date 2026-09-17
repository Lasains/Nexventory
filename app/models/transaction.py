from app.extensions import db
from datetime import datetime


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'sale' or 'purchase'
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Payment fields (Midtrans integration)
    payment_method = db.Column(db.String(20), nullable=True)        # 'qris' or 'bank_transfer'
    payment_status = db.Column(db.String(20), nullable=True, default='pending')  # pending, settlement, expire, failure, cancel
    midtrans_order_id = db.Column(db.String(100), nullable=True, index=True)     # Order ID sent to Midtrans
    midtrans_transaction_id = db.Column(db.String(100), nullable=True)           # Transaction ID from Midtrans
    va_number = db.Column(db.String(50), nullable=True)              # Virtual Account number (bank transfer)
    va_bank = db.Column(db.String(20), nullable=True)                # Bank name (BCA, BNI, BRI, Mandiri)
    qris_string = db.Column(db.Text, nullable=True)                  # QR string from Midtrans QRIS
    paid_at = db.Column(db.DateTime, nullable=True)                  # Timestamp when payment settled

    product = db.relationship('Product', backref=db.backref('transactions', lazy=True))
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

    @property
    def timestamp(self):
        return self.created_at

    @property
    def is_paid(self) -> bool:
        return self.payment_status in ('settlement', 'capture')

    def __repr__(self):
        return f'<Transaction {self.id}>'