"""
HotelBook Pro - Configuración Centralizada
Entornos: development, testing, production
"""

import os
import secrets
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _get_secret_key() -> str:
    """SECRET_KEY: genera aleatorio en dev, error claro en prod."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    if os.environ.get("FLASK_ENV") == "production":
        raise ValueError(
            "SECRET_KEY no está configurada. "
            "Establece SECRET_KEY en variables de entorno para producción."
        )
    return secrets.token_hex(32)


def _get_database_uri() -> str:
    """Construye la URL de BD desde variables separadas o URL completa."""
    url = os.environ.get("DATABASE_URL", "")
    if url:
        return url

    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "hotelbook")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "")

    db_url = f"postgresql://{user}:{password}@{host}:{port}/{name}" if password \
        else f"postgresql://{user}@{host}:{port}/{name}"
    return db_url


class Config:
    """Configuración base compartida por todos los entornos."""
    SECRET_KEY = _get_secret_key()
    JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", 24))
    BCRYPT_LOG_ROUNDS = int(os.environ.get("BCRYPT_LOG_ROUNDS", 12))
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "")
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    ITEMS_PER_PAGE = 20
    IVA_RATE = 0.19
    PUNTOS_POR_NOCHE = 10
    GARANTIA_PORCENTAJE = 0.50
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    ADMIN_BOOTSTRAP_ENABLED = os.environ.get("ADMIN_BOOTSTRAP_ENABLED", "False") == "True"
    ADMIN_BOOTSTRAP_SECRET = os.environ.get("ADMIN_BOOTSTRAP_SECRET", "")
    PERMANENT_SESSION_LIFETIME = 86400  # 24 horas en segundos


class DevelopmentConfig(Config):
    """Entorno de desarrollo: PostgreSQL o SQLite fallback."""
    DEBUG = True
    STRIPE_MOCK = True
    SQLALCHEMY_DATABASE_URI = (
        _get_database_uri()
        if os.environ.get("DB_HOST") or os.environ.get("DATABASE_URL")
        else f"sqlite:///{os.path.join(BASE_DIR, 'hotelbook_dev.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Entorno de pruebas: SQLite en memoria."""
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
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CORS_ORIGINS = (
        os.environ.get("CORS_ORIGINS", "").split(",")
        if os.environ.get("CORS_ORIGINS") else []
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
    }


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
