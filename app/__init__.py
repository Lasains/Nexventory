# app/__init__.py
import os
from flask import Flask
from flask_migrate import Migrate
from config import Config

# Import extensions
from app.extensions import db, login_manager, migrate, oauth

def create_app(config_class=Config):
    # Get the parent directory of the app module
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(basedir, 'templates'),
                static_folder=os.path.join(basedir, 'static'))
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'
    # Init oauth with app
    oauth.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import bp as main_bp
    from app.routes.admin import admin_bp
    from app.routes.user import user_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')

    # Import models after db is initialized
    from app.models.user import User
    from app.models.product import Product
    from app.models.transaction import Transaction

    # Auto-create tables if missing
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Could not auto-create tables: {e}")

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))