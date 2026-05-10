"""
HotelBook Pro - Configuración global de pytest
Fixtures compartidas por todos los tests
"""

import pytest
from app import create_app, db as _db


@pytest.fixture(scope="session")
def app():
    """Crea la app en modo testing (SQLite en memoria)."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Cliente HTTP para hacer requests en los tests."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Sesión de BD limpia por cada test."""
    with app.app_context():
        yield _db
        _db.session.rollback()