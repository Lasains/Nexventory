# app/routes/__init__.py
from flask import Blueprint

# Create the main blueprint
bp = Blueprint('main', __name__)

# Import routes after creating the blueprint to avoid circular imports
from app.routes import auth
from app.routes import main