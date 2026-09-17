from app.extensions import db

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'sale' or 'purchase'
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    product = db.relationship('Product', backref=db.backref('transactions', lazy=True))
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    
    @property
    def timestamp(self):
        return self.created_at
    
    def __repr__(self):
        return f'<Transaction {self.id}>'