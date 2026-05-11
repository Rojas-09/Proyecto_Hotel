"""
HotelBook Pro - Configuración global de pytest
Fixtures compartidas por todos los tests
"""

import pytest
from app import create_app, db as _db


@pytest.fixture(scope="function")
def app():
    """Crea una app de testing aislada por prueba (SQLite en memoria)."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Cliente HTTP para hacer requests en los tests."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Acceso a la BD de testing para cada test."""
    with app.app_context():
        yield _db
        _db.session.rollback()