"""
HotelBook Pro - Configuración global de pytest
Fixtures compartidas por todos los tests
"""

import pytest
from app import create_app, db as _db
from app.models.usuario import Usuario, RolEnum
from app.models.huesped import Huesped


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


@pytest.fixture(scope="function")
def cliente(app):
    """Crea un usuario cliente con su Huesped asociado."""
    with app.app_context():
        usuario = Usuario(
            nombre="Juan",
            apellido="Pérez",
            email="cliente@test.com",
            telefono="3012345678",
            rol=RolEnum.cliente,
        )
        usuario.password = "password123"
        _db.session.add(usuario)
        _db.session.flush()

        huesped = Huesped(
            id_usuario=usuario.id,
            documento_id="12345678",
            tipo_documento="CC",
            preferencias="Sin preferencias",
        )
        _db.session.add(huesped)
        _db.session.commit()

        return usuario


@pytest.fixture(scope="function")
def admin(app):
    """Crea un usuario administrador."""
    with app.app_context():
        usuario = Usuario(
            nombre="Admin",
            apellido="User",
            email="admin@test.com",
            telefono="3011111111",
            rol=RolEnum.admin,
        )
        usuario.password = "admin123456"
        _db.session.add(usuario)
        _db.session.commit()

        return usuario


@pytest.fixture(scope="function")
def cliente_headers(client, cliente):
    """Headers de autenticación para un cliente existente."""
    res = client.post("/api/v1/auth/login", json={
        "email": "cliente@test.com",
        "password": "password123",
    })
    token = _extract_token_from_cookies(client)
    return {"Authorization": f"Bearer {token}"}


def _extract_token_from_cookies(client):
    """Lee el access_token del test client tras un login exitoso."""
    cookie = client.get_cookie("access_token")
    return cookie.value if cookie else None