"""Tests para session_helper.py — decoradores login_required y roles_allowed."""

from unittest.mock import patch


class MockF:
    def __call__(self, *args, **kwargs):
        return "ok"

    def __repr__(self):
        return "mock_f"


class TestLoginRequired:

    def setup_method(self):
        from app.utils.session_helper import login_required
        self.decorated = login_required(MockF())

    def test_sin_sesion(self, app):
        with patch("app.utils.session_helper.session", {}), \
             patch("app.utils.session_helper.flash") as mf, \
             patch("app.utils.session_helper.redirect") as mr, \
             patch("app.utils.session_helper.url_for") as mu:
            mr.return_value = "redirected"
            mu.return_value = "/login"
            assert self.decorated() == "redirected"
            mf.assert_called_once()

    def test_con_sesion_valida(self, app):
        with patch("app.utils.session_helper.session",
                   {"user_id": 1}), \
             patch("app.utils.session_helper._revalidar_usuario",
                   return_value=True):
            assert self.decorated() == "ok"

    def test_usuario_desactivado(self, app):
        with patch("app.utils.session_helper.session",
                   {"user_id": 1}), \
             patch("app.utils.session_helper._revalidar_usuario",
                   return_value=False), \
             patch("app.utils.session_helper.flash") as mf, \
             patch("app.utils.session_helper.redirect") as mr, \
             patch("app.utils.session_helper.url_for") as mu:
            mr.return_value = "redirected"
            mu.return_value = "/login"
            assert self.decorated() == "redirected"
            mf.assert_called_with("Su cuenta ha sido desactivada.", "warning")


class TestRolesAllowed:

    def setup_method(self):
        from app.utils.session_helper import roles_allowed
        self.decorated = roles_allowed("admin", "gerente")(MockF())

    def test_sin_sesion(self, app):
        with patch("app.utils.session_helper.session", {}), \
             patch("app.utils.session_helper.flash") as mf, \
             patch("app.utils.session_helper.redirect") as mr, \
             patch("app.utils.session_helper.url_for") as mu:
            mr.return_value = "redirected"
            mu.return_value = "/login"
            assert self.decorated() == "redirected"
            mf.assert_called_once()

    def test_usuario_desactivado(self, app):
        with patch("app.utils.session_helper.session",
                   {"user_id": 1, "user_rol": "admin"}), \
             patch("app.utils.session_helper._revalidar_usuario",
                   return_value=False), \
             patch("app.utils.session_helper.flash"), \
             patch("app.utils.session_helper.redirect") as mr, \
             patch("app.utils.session_helper.url_for") as mu:
            mr.return_value = "redirected"
            mu.return_value = "/login"
            assert self.decorated() == "redirected"

    def test_rol_no_permitido(self, app):
        with patch("app.utils.session_helper.session",
                   {"user_id": 1, "user_rol": "cliente"}), \
             patch("app.utils.session_helper._revalidar_usuario",
                   return_value=True), \
             patch("app.utils.session_helper.flash") as mf, \
             patch("app.utils.session_helper.redirect") as mr, \
             patch("app.utils.session_helper.url_for") as mu:
            mr.return_value = "redirected"
            mu.return_value = "/home"
            assert self.decorated() == "redirected"
            mf.assert_called_once()

    def test_rol_permitido(self, app):
        with patch("app.utils.session_helper.session",
                   {"user_id": 1, "user_rol": "admin"}), \
             patch("app.utils.session_helper._revalidar_usuario",
                   return_value=True):
            assert self.decorated() == "ok"