"""
HotelBook Pro - Configuración Centralizada
Entornos: development, testing, production
"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_uri():
    """Construye la URL de BD desde variables separadas o URL completa."""
    url = os.environ.get("DATABASE_URL", "")
    if url:
        return url

    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "hotelbook")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "")

    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    return f"postgresql://{user}@{host}:{port}/{name}"


class Config:
    """Configuración base compartida por todos los entornos."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambia-esto-en-produccion")
    JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", 24))
    BCRYPT_LOG_ROUNDS = int(os.environ.get("BCRYPT_LOG_ROUNDS", 12))

    # Stripe
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "")

    # Email (SMTP nativo)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

    # Paginación
    ITEMS_PER_PAGE = 20

    # IVA Colombia
    IVA_RATE = 0.19

    # Fidelización
    PUNTOS_POR_NOCHE = 10

    # Garantía de reserva
    GARANTIA_PORCENTAJE = 0.50


class DevelopmentConfig(Config):
    """Entorno de desarrollo: PostgreSQL (si DB_* configurado) o SQLite."""
    DEBUG = True
    STRIPE_MOCK = True
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

    # Si hay variables DB_* configuradas, usa PostgreSQL; si no, SQLite
    if os.environ.get("DB_HOST") or os.environ.get("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = get_database_uri()
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'hotelbook_dev.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Entorno de pruebas: SQLite en memoria, sin bcrypt costoso."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_LOG_ROUNDS = 4
    WTF_CSRF_ENABLED = False
    STRIPE_MOCK = True
    STRIPE_SECRET_KEY = None


class ProductionConfig(Config):
    """Entorno de producción: PostgreSQL, debug desactivado."""
    DEBUG = False
    STRIPE_MOCK = False
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Seguridad adicional en producción
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True


config = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}