"""Tests para session_helper.py — decoradores login_required y roles_allowed."""

from unittest.mock import patch, MagicMock


class MockF:
    def __call__(self, *args, **kwargs):
        return "ok"

    def __repr__(self):
        return "mock_f"


def _mock_urlfor(endpoint, **kwargs):
    return f"/{endpoint.replace('.', '/')}"


class TestLoginRequired:

    def setup_method(self):
        from app.utils.session_helper import login_required
        self.decorated = login_required(MockF())

    def test_sin_sesion(self, app):
        """Sin user_id en session → flash + redirect."""
        with patch("app.utils.session_helper.session", {}), \
             patch("app.utils.session_helper.flash") as mock_flash, \
             patch("app.utils.session_helper.redirect") as mock_redirect, \
             patch("app.utils.session_helper.url_for") as mock_urlfor:
            mock_redirect.return_value = "redirected"
            mock_urlfor.return_value = "/login"
            result = self.decorated()
            mock_flash.assert_called_once_with(
                "Por favor inicie sesión para acceder.", "warning"
            )
            assert result == "redirected"

    def test_con_sesion(self):
        """Con user_id en session → ejecuta función original."""
        with patch("app.utils.session_helper.session", {"user_id": 1}):
            result = self.decorated()
            assert result == "ok"


class TestRolesAllowed:

    def setup_method(self):
        from app.utils.session_helper import roles_allowed
        self.decorated = roles_allowed("admin", "gerente")(MockF())

    def test_sin_rol_en_sesion(self, app):
        """Sin user_rol en session → flash + redirect."""
        with patch("app.utils.session_helper.session", {}), \
             patch("app.utils.session_helper.flash") as mock_flash, \
             patch("app.utils.session_helper.redirect") as mock_redirect, \
             patch("app.utils.session_helper.url_for") as mock_urlfor:
            mock_redirect.return_value = "redirected"
            mock_urlfor.return_value = "/home"
            result = self.decorated()
            mock_flash.assert_called_once_with(
                "No tiene permisos para acceder a esta sección.", "danger"
            )
            assert result == "redirected"

    def test_rol_no_permitido(self, app):
        """Rol no permitido → flash + redirect."""
        with patch("app.utils.session_helper.session", {"user_rol": "cliente"}), \
             patch("app.utils.session_helper.flash") as mock_flash, \
             patch("app.utils.session_helper.redirect") as mock_redirect, \
             patch("app.utils.session_helper.url_for") as mock_urlfor:
            mock_redirect.return_value = "redirected"
            mock_urlfor.return_value = "/home"
            result = self.decorated()
            mock_flash.assert_called_once()
            assert result == "redirected"

    def test_rol_permitido(self):
        """Rol permitido → ejecuta función original."""
        with patch("app.utils.session_helper.session", {"user_rol": "admin"}):
            result = self.decorated()
            assert result == "ok"