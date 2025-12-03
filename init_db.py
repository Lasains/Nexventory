from app import create_app, db
from app.models import User  # Make sure to import all your models

app = create_app()

with app.app_context():
    # This will create all tables
    db.create_all()
    
    # Check if admin user already exists
    existing_admin = User.query.filter_by(username='admin').first()
    if not existing_admin:
        # Create an admin user (optional)
        admin = User(
            username='admin',
            email='admin@example.com',
            password='admin123',  # This will be hashed automatically
            role='admin'
        )                                                                                       
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists!")