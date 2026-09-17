from app import create_app, db
from app.models import User  # Make sure to import all your models

app = create_app()

with app.app_context():
    # This will create all tables
    db.create_all()
    
    # Check if admin user already exists
    existing_admin = User.query.filter_by(username='admin').first()
    if not existing_admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        db.session.add(admin)
        print("Admin user created successfully!")

    # Check if test regular user exists
    existing_user = User.query.filter_by(username='user').first()
    if not existing_user:
        test_user = User(
            username='user',
            email='user@example.com',
            password='user123',
            role='user'
        )
        db.session.add(test_user)
        print("Test user created successfully!")

    # Check and add sample products
    from app.models.product import Product
    if Product.query.count() == 0:
        sample_products = [
            Product(name='Wireless Bluetooth Headphone Pro', category='Elektronik', price=250000.0, stock=25, min_stock=5),
            Product(name='Mechanical Gaming Keyboard RGB', category='Elektronik', price=450000.0, stock=15, min_stock=3),
            Product(name='Ergonomic Mouse Wireless 2.4G', category='Elektronik', price=120000.0, stock=30, min_stock=5),
            Product(name='Backpack Laptop Waterproof 15.6"', category='Aksesoris', price=185000.0, stock=20, min_stock=4),
            Product(name='Stainless Steel Tumbler 500ml', category='Peralatan', price=75000.0, stock=50, min_stock=10),
        ]
        db.session.add_all(sample_products)
        print(f"Added {len(sample_products)} sample products!")

    db.session.commit()
    print("Database initialization completed!")