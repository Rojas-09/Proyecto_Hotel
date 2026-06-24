"""
HotelBook Pro - Punto de entrada de la aplicación
Uso: flask run  |  python run.py
"""

import os
from app import create_app

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    # Solo desarrollo local — usar gunicorn/uWSGI en producción (host 0.0.0.0)
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5000)),
        debug=(env == "development"),
    )
