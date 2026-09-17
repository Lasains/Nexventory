import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()
app = create_app()

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
    app.run(debug=True, port=5000)