# main.py - fallback entrypoint for platforms expecting main:app
from wsgi import app

if __name__ == '__main__':
    app.run()
