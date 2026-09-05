import os
from dotenv import load_dotenv
from flask import render_template
from flask_login import LoginManager
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.user import user_bp
from app.routes.main import bp as main_bp
from app.models.user import User
from app.extensions import login_manager
from app import create_app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

# Route untuk halaman utama
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Run auto-migration before starting the app
    try:
        import subprocess
        print("🔄 Checking for database changes...")
        result = subprocess.run(['python3', 'auto_migrate.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("⚠️  Migration check failed, starting app anyway...")
    except Exception as e:
        print(f"⚠️  Could not run auto-migration: {e}")
    
    print("🚀 Starting Flask application...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)