"""
Tests - Módulo Auth
Cubre: register, login, /me, protección por rol
"""

import pytest
from app.models.usuario import Usuario, RolEnum
from app.models.huesped import Huesped


@pytest.fixture
def usuario_cliente(db):
    """Crea un cliente con su Huesped."""
    u = Usuario(
        nombre="Ana", apellido="García", email="ana@test.com", rol=RolEnum.cliente
    )
    u.password = "Password123"
    db.session.add(u)
    db.session.flush()

    h = Huesped(id_usuario=u.id, documento_id="87654321", tipo_documento="CC")
    db.session.add(h)
    db.session.commit()
    return u


@pytest.fixture
def usuario_admin(db):
    """Crea un admin (sin Huesped)."""
    u = Usuario(
        nombre="Admin", apellido="Hotel", email="admin@test.com", rol=RolEnum.admin
    )
    u.password = "AdminPass123"
    db.session.add(u)
    db.session.commit()
    return u


def obtener_token(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    set_cookie = res.headers.get("Set-Cookie", "")
    for part in set_cookie.split(";"):
        part = part.strip()
        if part.startswith("access_token="):
            return part.split("access_token=", 1)[1]
    return None


class TestRegister:

    def test_registro_exitoso(self, client):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "nombre": "Juan",
                "apellido": "Rojas",
                "email": "juan@test.com",
                "password": "Segura123",
                "documento_id": "12345678",
                "tipo_documento": "CC",
            },
        )
        data = res.get_json()
        assert res.status_code == 201
        assert data["success"] is True
        assert "token" not in data["data"]
        assert data["data"]["usuario"]["rol"] == "cliente"

    def test_registro_email_duplicado(self, client, usuario_cliente):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "nombre": "Otra",
                "apellido": "Persona",
                "email": "ana@test.com",
                "password": "OtraPass123",
                "documento_id": "99999999",
            },
        )
        assert res.status_code == 409
        assert res.get_json()["error"]["code"] == "CONFLICT"

    def test_registro_password_corta(self, client):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "nombre": "Test",
                "apellido": "Test",
                "email": "nuevo@test.com",
                "password": "123",
                "documento_id": "11111111",
            },
        )
        assert res.status_code == 422
        assert res.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_registro_campo_faltante(self, client):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "nombre": "Test",
                "email": "otro@test.com",
                "documento_id": "22222222",
            },
        )
        assert res.status_code == 422

    def test_registro_sin_documento_id(self, client):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "nombre": "Test",
                "apellido": "User",
                "email": "test@test.com",
                "password": "Password123",
            },
        )
        assert res.status_code == 400
        assert "documento_id" in res.get_json()["error"]["message"]

    def test_registro_sin_body(self, client):
        res = client.post("/api/v1/auth/register")
        assert res.status_code == 422


class TestLogin:

    def test_login_exitoso(self, client, usuario_cliente):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "ana@test.com", "password": "Password123"},
        )
        data = res.get_json()
        assert res.status_code == 200
        assert data["success"] is True
        assert "token" not in data["data"]

    def test_login_password_incorrecta(self, client, usuario_cliente):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "ana@test.com", "password": "Incorrecta99"},
        )
        assert res.status_code == 401
        assert res.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_login_email_inexistente(self, client):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "noexiste@test.com", "password": "Cualquiera1"},
        )
        assert res.status_code == 401

    def test_login_sin_body(self, client):
        res = client.post("/api/v1/auth/login")
        assert res.status_code == 422


class TestMe:

    def test_me_con_token_valido(self, client, usuario_cliente):
        token = obtener_token(client, "ana@test.com", "Password123")
        res = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        data = res.get_json()
        assert res.status_code == 200
        assert data["data"]["usuario"]["email"] == "ana@test.com"

    def test_me_sin_token(self, client):
        res = client.get("/api/v1/auth/me")
        assert res.status_code == 401

    def test_me_token_invalido(self, client):
        res = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer token.falso.aqui"}
        )
        assert res.status_code == 401


class TestCrearUsuario:

    def test_admin_puede_crear_recepcionista(self, client, usuario_admin):
        token = obtener_token(client, "admin@test.com", "AdminPass123")
        res = client.post(
            "/api/v1/auth/usuarios",
            json={
                "nombre": "Carlos",
                "apellido": "Lopez",
                "email": "carlos@hotel.com",
                "password": "Recep1234",
                "rol": "recepcionista",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        data = res.get_json()
        assert res.status_code == 201
        assert data["data"]["usuario"]["rol"] == "recepcionista"

    def test_cliente_no_puede_crear_usuarios(self, client, usuario_cliente):
        token = obtener_token(client, "ana@test.com", "Password123")
        res = client.post(
            "/api/v1/auth/usuarios",
            json={
                "nombre": "X",
                "apellido": "Y",
                "email": "x@test.com",
                "password": "Pass1234",
                "rol": "admin",
                "documento_id": "33333333",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert res.get_json()["error"]["code"] == "FORBIDDEN"
