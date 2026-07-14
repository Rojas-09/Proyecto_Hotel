"""Cubre los except Exception / ValueError / PermissionError
   de notificacion_controller, huesped_controller y pago_controller
   que no se alcanzan por flujo normal."""

import pytest
from unittest.mock import patch

from app import db
from app.models.usuario import RolEnum, Usuario
from app.utils.jwt_helper import generar_token


@pytest.fixture
def admin_token(app):
    with app.app_context():
        u = Usuario(nombre="A", apellido="B", email="exc_adm@test.com", rol=RolEnum.admin)
        u.password = "X"
        db.session.add(u)
        db.session.commit()
        return generar_token(u.id, u.email, "admin")


class TestNotificacionControllerExcepciones:
    @patch("app.services.notificacion_service.listar")
    def test_listar_exception_retorna_500(self, mock_listar, client, admin_token):
        mock_listar.side_effect = RuntimeError("DB error")
        resp = client.get("/api/v1/notificaciones",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 500

    @patch("app.services.notificacion_service.buscar")
    def test_buscar_value_error_retorna_400(self, mock_buscar, client, admin_token):
        mock_buscar.side_effect = ValueError("bad query")
        resp = client.get("/api/v1/notificaciones/buscar?q=test",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 400

    @patch("app.services.notificacion_service.buscar")
    def test_buscar_exception_retorna_500(self, mock_buscar, client, admin_token):
        mock_buscar.side_effect = RuntimeError("DB error")
        resp = client.get("/api/v1/notificaciones/buscar?q=test",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 500


class TestHuespedControllerExcepciones:
    @patch("app.services.huesped_service.eliminar")
    def test_eliminar_exception_retorna_500(self, mock_eliminar, client, admin_token):
        mock_eliminar.side_effect = RuntimeError("DB error")
        resp = client.delete("/api/v1/huespedes/1",
                             headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 500

    @patch("app.services.huesped_service.obtener_todos")
    def test_obtener_todos_exception_retorna_500(self, mock_list, client, admin_token):
        mock_list.side_effect = RuntimeError("DB error")
        resp = client.get("/api/v1/huespedes/",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 500

    @patch("app.services.huesped_service.obtener_por_id")
    def test_obtener_por_id_exception_retorna_500(self, mock_get, client, admin_token):
        mock_get.side_effect = RuntimeError("DB error")
        resp = client.get("/api/v1/huespedes/1",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 500

    @patch("app.services.huesped_service.buscar")
    def test_buscar_value_error_retorna_400(self, mock_buscar, client, admin_token):
        mock_buscar.side_effect = ValueError("bad query")
        resp = client.get("/api/v1/huespedes/buscar?q=test",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 400

    @patch("app.services.huesped_service.buscar")
    def test_buscar_exception_retorna_500(self, mock_buscar, client, admin_token):
        mock_buscar.side_effect = RuntimeError("DB error")
        resp = client.get("/api/v1/huespedes/buscar?q=test",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 500

    @patch("app.services.huesped_service.actualizar")
    def test_actualizar_exception_retorna_500(self, mock_act, client, admin_token):
        mock_act.side_effect = RuntimeError("DB error")
        resp = client.put("/api/v1/huespedes/1",
                          json={"documento_id": "123"},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 500


class TestPagoControllerExcepciones:
    @patch("app.services.pago_service.procesar_garantia")
    def test_garantia_lookup_error_retorna_404(self, mock_proc, client, app):
        mock_proc.side_effect = LookupError("reserva no encontrada")
        with app.app_context():
            u = Usuario(nombre="R", apellido="T", email="exc_pag@test.com", rol=RolEnum.admin)
            u.password = "X"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.post("/api/v1/pagos/garantia/99999",
                           json={"metodo": "Efectivo"},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    @patch("app.services.pago_service.procesar_garantia")
    def test_garantia_permission_error_retorna_403(self, mock_proc, client, app):
        mock_proc.side_effect = PermissionError("sin permiso")
        with app.app_context():
            u = Usuario(nombre="R2", apellido="T", email="exc_pag2@test.com", rol=RolEnum.admin)
            u.password = "X"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.post("/api/v1/pagos/garantia/1",
                           json={"metodo": "Efectivo"},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    @patch("app.services.pago_service.confirmar_pago_manual")
    def test_confirmar_lookup_error_retorna_404(self, mock_conf, client, app):
        mock_conf.side_effect = LookupError("pago no encontrado")
        with app.app_context():
            u = Usuario(nombre="R3", apellido="T", email="exc_pag3@test.com", rol=RolEnum.admin)
            u.password = "X"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.put("/api/v1/pagos/99999/confirmar",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    @patch("app.services.pago_service.confirmar_pago_manual")
    def test_confirmar_value_error_retorna_400(self, mock_conf, client, app):
        mock_conf.side_effect = ValueError("pago ya confirmado")
        with app.app_context():
            u = Usuario(nombre="R4", apellido="T", email="exc_pag4@test.com", rol=RolEnum.admin)
            u.password = "X"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.put("/api/v1/pagos/1/confirmar",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400

    @patch("app.services.pago_service.confirmar_pago_manual")
    def test_confirmar_exito_retorna_200(self, mock_conf, client, app):
        mock_conf.return_value = {"id": 1, "estado": "Aprobado"}
        with app.app_context():
            u = Usuario(nombre="R5", apellido="T", email="exc_pag5@test.com", rol=RolEnum.admin)
            u.password = "X"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.put("/api/v1/pagos/1/confirmar",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_liquidacion_validation_error_retorna_422(self, client, app):
        with app.app_context():
            u = Usuario(nombre="R6", apellido="T", email="exc_pag6@test.com", rol=RolEnum.admin)
            u.password = "X"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.post("/api/v1/pagos/liquidacion/1",
                           json={},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 422

    @patch("app.services.stripe_webhook_service.procesar_evento")
    def test_webhook_exito_retorna_200(self, mock_proc, client):
        mock_proc.return_value = {"tipo": "payment_intent.succeeded", "procesado": True, "detalle": "ok"}
        resp = client.post("/api/v1/pagos/webhook",
                           data=b"{}", content_type="application/json",
                           headers={"Stripe-Signature": "test"})
        assert resp.status_code == 200

    @patch("app.services.pago_service.listar")
    def test_listar_pagos_value_error_retorna_400(self, mock_list, client, app):
        mock_list.side_effect = ValueError("bad filter")
        with app.app_context():
            u = Usuario(nombre="R7", apellido="T", email="exc_pag7@test.com", rol=RolEnum.admin)
            u.password = "X"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.get("/api/v1/pagos?estado=invalido",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400

    @patch("app.services.pago_service.listar")
    def test_listar_pagos_exception_retorna_500(self, mock_list, client, app):
        mock_list.side_effect = RuntimeError("DB error")
        with app.app_context():
            u = Usuario(nombre="R8", apellido="T", email="exc_pag8@test.com", rol=RolEnum.admin)
            u.password = "X"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.get("/api/v1/pagos?estado=Pendiente",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 500

    @patch("app.services.pago_service.anular")
    def test_eliminar_pago_value_error_retorna_400(self, mock_anular, client, app):
        mock_anular.side_effect = ValueError("pago no anulable")
        with app.app_context():
            u = Usuario(nombre="R9", apellido="T", email="exc_pag9@test.com", rol=RolEnum.admin)
            u.password = "X"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.delete("/api/v1/pagos/1",
                             json={"motivo": "test"},
                             headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400
