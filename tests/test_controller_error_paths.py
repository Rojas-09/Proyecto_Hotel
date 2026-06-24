from tests.conftest import _extract_token_from_cookies
from app import db
from app.models.usuario import Usuario, RolEnum
from app.models.huesped import Huesped


def _token_para(client, app, email, rol="admin"):
    with app.app_context():
        u = Usuario(
            nombre="T",
            apellido="User",
            email=email,
            rol=RolEnum.admin if rol == "admin" else RolEnum.cliente,
        )
        u.password = "Password123"
        db.session.add(u)
        db.session.flush()

        # Si es cliente, crear Huesped automáticamente
        if rol == "cliente":
            h = Huesped(id_usuario=u.id, documento_id="99999999", tipo_documento="CC")
            db.session.add(h)

        db.session.commit()
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"},
    )
    return _extract_token_from_cookies(client)


def test_habitaciones_listar_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "ha_err@test.com", "admin")

    def _boom(_):
        raise RuntimeError("boom")

    target = "app.controllers.habitacion_controller.habitacion_service.obtener_todas"
    monkeypatch.setattr(target, _boom)
    resp = client.get(
        "/api/v1/habitaciones/", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 500


def test_habitaciones_disponibles_error_500(client, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    target = (
        "app.controllers.habitacion_controller.habitacion_service.buscar_disponibles"
    )
    monkeypatch.setattr(target, _boom)
    resp = client.get(
        "/api/v1/habitaciones/disponibles?fecha_entrada=2027-01-01&fecha_salida=2027-01-02",
    )
    assert resp.status_code == 500


def test_habitaciones_obtener_error_500(client, monkeypatch):
    def _boom(_):
        raise RuntimeError("boom")

    target = "app.controllers.habitacion_controller.habitacion_service.obtener_por_id"
    monkeypatch.setattr(target, _boom)
    resp = client.get("/api/v1/habitaciones/1")
    assert resp.status_code == 500


def test_habitaciones_crear_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "ha1@test.com", "admin")

    def _boom(_):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.controllers.habitacion_controller.habitacion_service.crear", _boom
    )
    resp = client.post(
        "/api/v1/habitaciones/",
        json={
            "numero": "999",
            "tipo": "simple",
            "precio_noche": 100,
            "capacidad": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 500


def test_habitaciones_actualizar_body_requerido(client, app):
    token = _token_para(client, app, "ha2@test.com", "admin")
    resp = client.put(
        "/api/v1/habitaciones/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 415


def test_habitaciones_actualizar_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "ha3@test.com", "admin")

    def _boom(_id, _data):
        raise RuntimeError("boom")

    target = "app.controllers.habitacion_controller.habitacion_service.actualizar"
    monkeypatch.setattr(target, _boom)
    resp = client.put(
        "/api/v1/habitaciones/1",
        json={"precio_noche": 99999},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 500


def test_habitaciones_eliminar_valor_error(client, app, monkeypatch):
    token = _token_para(client, app, "ha4@test.com", "admin")

    def _val(_id):
        raise ValueError("invalido")

    monkeypatch.setattr(
        "app.controllers.habitacion_controller.habitacion_service.eliminar", _val
    )
    resp = client.delete(
        "/api/v1/habitaciones/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_habitaciones_eliminar_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "ha5@test.com", "admin")

    def _boom(_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.controllers.habitacion_controller.habitacion_service.eliminar", _boom
    )
    resp = client.delete(
        "/api/v1/habitaciones/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 500


def test_reservas_crear_body_requerido(client, app):
    token = _token_para(client, app, "re1@test.com", "cliente")
    resp = client.post(
        "/api/v1/reservas/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 415


def test_reservas_crear_permission_error(client, app, monkeypatch):
    token = _token_para(client, app, "re2@test.com", "cliente")

    def _perm(_data, _user):
        raise PermissionError("no")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.crear", _perm
    )
    resp = client.post(
        "/api/v1/reservas/",
        json={
            "id_habitacion": 1,
            "fecha_entrada": "2027-01-01",
            "fecha_salida": "2027-01-02",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_reservas_crear_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "re3@test.com", "cliente")

    def _boom(_data, _user):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.crear", _boom
    )
    resp = client.post(
        "/api/v1/reservas/",
        json={
            "id_habitacion": 1,
            "fecha_entrada": "2027-01-01",
            "fecha_salida": "2027-01-02",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 500


def test_reservas_obtener_todas_valor_error(client, app, monkeypatch):
    token = _token_para(client, app, "re4@test.com", "admin")

    def _val(_filtros):
        raise ValueError("bad")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.obtener_todas", _val
    )
    resp = client.get(
        "/api/v1/reservas/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_reservas_obtener_todas_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "re5@test.com", "admin")

    def _boom(_filtros):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.obtener_todas", _boom
    )
    resp = client.get(
        "/api/v1/reservas/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 500


def test_reservas_mis_reservas_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "re6@test.com", "cliente")

    def _boom(_user):
        raise RuntimeError("boom")

    target = "app.controllers.reserva_controller.reserva_service.obtener_mis_reservas"
    monkeypatch.setattr(target, _boom)
    resp = client.get(
        "/api/v1/reservas/mis-reservas",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 500


def test_reservas_obtener_por_id_lookup_error(client, app, monkeypatch):
    token = _token_para(client, app, "re7@test.com", "admin")

    def _lk(_id, _user):
        raise LookupError("no")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.obtener_por_id", _lk
    )
    resp = client.get(
        "/api/v1/reservas/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_reservas_obtener_por_id_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "re8@test.com", "admin")

    def _boom(_id, _user):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.obtener_por_id", _boom
    )
    resp = client.get(
        "/api/v1/reservas/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 500


def test_reservas_confirmar_lookup_y_error(client, app, monkeypatch):
    token = _token_para(client, app, "re9@test.com", "admin")

    def _lk(_id):
        raise LookupError("no")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.confirmar", _lk
    )
    resp_lk = client.put(
        "/api/v1/reservas/1/confirmar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_lk.status_code == 404

    def _boom(_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.confirmar", _boom
    )
    resp_boom = client.put(
        "/api/v1/reservas/1/confirmar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_boom.status_code == 500


def test_reservas_cancelar_lookup_permission_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "re10@test.com", "cliente")

    def _lk(_id, _motivo, _user):
        raise LookupError("no")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.cancelar", _lk
    )
    resp_lk = client.put(
        "/api/v1/reservas/1/cancelar",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_lk.status_code == 404

    def _perm(_id, _motivo, _user):
        raise PermissionError("forbidden")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.cancelar", _perm
    )
    resp_perm = client.put(
        "/api/v1/reservas/1/cancelar",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_perm.status_code == 403

    def _boom(_id, _motivo, _user):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.cancelar", _boom
    )
    resp_boom = client.put(
        "/api/v1/reservas/1/cancelar",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_boom.status_code == 500


def test_reservas_checkin_lookup_valor_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "re11@test.com", "admin")

    def _lk(_id, **kwargs):
        raise LookupError("no")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.hacer_checkin", _lk
    )
    resp_lk = client.put(
        "/api/v1/reservas/1/checkin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_lk.status_code == 404

    def _val(_id, **kwargs):
        raise ValueError("bad")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.hacer_checkin", _val
    )
    resp_val = client.put(
        "/api/v1/reservas/1/checkin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_val.status_code == 400

    def _boom(_id, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.hacer_checkin", _boom
    )
    resp_boom = client.put(
        "/api/v1/reservas/1/checkin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_boom.status_code == 500


def test_reservas_checkout_lookup_valor_error_500(client, app, monkeypatch):
    token = _token_para(client, app, "re12@test.com", "admin")

    def _lk(_id, **kwargs):
        raise LookupError("no")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.hacer_checkout", _lk
    )
    resp_lk = client.put(
        "/api/v1/reservas/1/checkout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_lk.status_code == 404

    def _val(_id, **kwargs):
        raise ValueError("bad")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.hacer_checkout", _val
    )
    resp_val = client.put(
        "/api/v1/reservas/1/checkout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_val.status_code == 400

    def _boom(_id, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.controllers.reserva_controller.reserva_service.hacer_checkout", _boom
    )
    resp_boom = client.put(
        "/api/v1/reservas/1/checkout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_boom.status_code == 500
