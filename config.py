# config.py
import os
from dotenv import load_dotenv

# Load environment variables
basedir = os.path.abspath(os.path.dirname(__file__))
# Don't override system/cloud environment variables with .env file
load_dotenv(os.path.join(basedir, '.env'), override=False)

def get_database_uri():
    """Smartly resolve database URI for both local development and cloud (Railway/Render)"""
    # 1. Check Railway MySQL specific variable
    mysql_url = os.environ.get('MYSQL_URL')
    if mysql_url:
        if mysql_url.startswith('mysql://'):
            return mysql_url.replace('mysql://', 'mysql+pymysql://', 1)
        return mysql_url

    # 2. Check individual Railway/MySQL host variable
    mysql_host = os.environ.get('MYSQLHOST') or os.environ.get('MYSQL_HOST')
    if mysql_host and mysql_host != 'localhost':
        user = os.environ.get('MYSQLUSER') or os.environ.get('MYSQL_USER') or 'root'
        password = os.environ.get('MYSQLPASSWORD') or os.environ.get('MYSQL_PASSWORD') or ''
        port = os.environ.get('MYSQLPORT') or os.environ.get('MYSQL_PORT') or '3306'
        database = os.environ.get('MYSQLDATABASE') or os.environ.get('MYSQL_DATABASE') or 'railway'
        return f"mysql+pymysql://{user}:{password}@{mysql_host}:{port}/{database}"

    # 3. Check DATABASE_URL (Railway, Heroku, Render)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('mysql://'):
            return database_url.replace('mysql://', 'mysql+pymysql://', 1)
        elif database_url.startswith('postgres://'):
            return database_url.replace('postgres://', 'postgresql://', 1)
        return database_url

    # 4. Check explicit SQLALCHEMY_DATABASE_URI
    sql_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    # In cloud environments (Railway, etc.), localhost MySQL is unreachable.
    is_cloud = bool(
        os.environ.get('RAILWAY_ENVIRONMENT') or 
        os.environ.get('RAILWAY_PROJECT_ID') or 
        os.environ.get('DYNO') or 
        os.environ.get('RENDER')
    )
    if is_cloud and sql_uri and ('localhost' in sql_uri or '127.0.0.1' in sql_uri):
        instance_dir = os.path.join(basedir, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        return 'sqlite:///' + os.path.join(instance_dir, 'nexventory.db')
        
    if sql_uri:
        if sql_uri.startswith('mysql://'):
            return sql_uri.replace('mysql://', 'mysql+pymysql://', 1)
        return sql_uri

    # 5. Default fallback to local SQLite
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    return 'sqlite:///' + os.path.join(instance_dir, 'nexventory.db')

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # Template and static folders
    TEMPLATE_FOLDER = os.path.join(basedir, 'templates')
    STATIC_FOLDER = os.path.join(basedir, 'static')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}