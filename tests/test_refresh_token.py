"""
Tests — Refresh Token revocable con rotación
"""

import pytest

from app import db
from app.models.usuario import Usuario, RolEnum
from app.models.refresh_token import RefreshToken


class TestRefreshTokenModel:

    def test_crear_y_verificar(self, app):
        with app.app_context():
            u = Usuario(
                nombre="Test",
                apellido="User",
                email="rt_model@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()

            token_plano, rt = RefreshToken.crear(u.id)
            db.session.commit()

            assert rt.id_usuario == u.id
            assert rt.revoked is False
            assert rt.id is not None

            verificado = RefreshToken.verificar(token_plano)
            assert verificado is not None
            assert verificado.id == rt.id

    def test_revocar(self, app):
        with app.app_context():
            u = Usuario(
                nombre="Rev",
                apellido="Test",
                email="rt_revoke@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()

            token_plano, rt = RefreshToken.crear(u.id)
            db.session.commit()
            rt_id = rt.id

            rt.revocar()
            db.session.commit()

            rt2 = db.session.get(RefreshToken, rt_id)
            assert rt2.revoked is True

            verificado = RefreshToken.verificar(token_plano)
            assert verificado is None

    def test_expirado_no_verifica(self, app):
        with app.app_context():
            u = Usuario(
                nombre="Exp",
                apellido="Test",
                email="rt_exp@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()

            token_plano, rt = RefreshToken.crear(u.id, dias=-1)
            db.session.commit()

            verificado = RefreshToken.verificar(token_plano)
            assert verificado is None


class TestRefreshTokenEndpoint:

    def _cookies_en_respuesta(self, resp):
        cookies = resp.headers.get_all("Set-Cookie")
        nombres = []
        for c in cookies:
            nombre = c.split("=", 1)[0]
            nombres.append(nombre)
        return nombres

    def test_login_retorna_cookies(self, client, app):
        with app.app_context():
            u = Usuario(
                nombre="Login",
                apellido="Test",
                email="rt_login@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()

        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "rt_login@test.com",
                "password": "Pass1234!",
            },
        )
        assert resp.status_code == 200
        cookies = self._cookies_en_respuesta(resp)
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    def test_refresh_exitoso(self, client, app):
        with app.app_context():
            u = Usuario(
                nombre="Refresh",
                apellido="Test",
                email="rt_refresh@test.com",
                rol=RolEnum.admin,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()

            token_plano, rt = RefreshToken.crear(u.id)
            db.session.commit()
            rt_id = rt.id

            client.set_cookie(
                "refresh_token",
                token_plano,
                path="/",
            )

        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["usuario"]["email"] == "rt_refresh@test.com"

        with app.app_context():
            rt_actualizado = db.session.get(RefreshToken, rt_id)
            assert rt_actualizado.revoked is True

    def test_refresh_con_token_invalido(self, client):
        client.set_cookie(
            "refresh_token",
            "token-invalido",
            path="/",
        )
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    def test_refresh_sin_token(self, client):
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    def test_logout_revoca_refresh(self, client, app):
        with app.app_context():
            u = Usuario(
                nombre="Logout",
                apellido="Test",
                email="rt_logout@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()

            token_plano, rt = RefreshToken.crear(u.id)
            db.session.commit()
            rt_id = rt.id

            client.set_cookie(
                "refresh_token",
                token_plano,
                path="/",
            )

        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200

        with app.app_context():
            rt_actualizado = db.session.get(RefreshToken, rt_id)
            assert rt_actualizado.revoked is True

    def test_register_retorna_cookies(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "nombre": "Nuevo",
                "apellido": "User",
                "email": "rt_register@test.com",
                "password": "Pass1234!",
                "documento_id": "RT-REG-001",
            },
        )
        assert resp.status_code == 201
        cookies = self._cookies_en_respuesta(resp)
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    def test_rotacion_previene_reuso(self, client, app):
        with app.app_context():
            u = Usuario(
                nombre="Rotar",
                apellido="Test",
                email="rt_rotate@test.com",
                rol=RolEnum.admin,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()

            token_plano, rt = RefreshToken.crear(u.id)
            db.session.commit()

            client.set_cookie(
                "refresh_token",
                token_plano,
                path="/",
            )

        resp1 = client.post("/api/v1/auth/refresh")
        assert resp1.status_code == 200

        client.set_cookie(
            "refresh_token",
            token_plano,
            path="/",
        )
        resp2 = client.post("/api/v1/auth/refresh")
        assert resp2.status_code == 401
