"""
Tests del Módulo Notificaciones - HotelBook Pro
Cubre: CRUD completo, búsqueda, filtros, permisos
"""

import pytest
from tests.conftest import _extract_token_from_cookies
from datetime import date, timedelta

from app.models.usuario import Usuario, RolEnum
from app.models.huesped import Huesped
from app.models.habitacion import Habitacion, TipoHabitacion, EstadoHabitacion
from app.models.reserva import Reserva, EstadoReserva
from app import db


@pytest.fixture
def admin_headers(client, app):
    with app.app_context():
        u = Usuario(
            nombre="Admin", apellido="Notif",
            email="admin_notif@test.com", rol=RolEnum.admin
        )
        u.password = "Admin1234"
        db.session.add(u)
        db.session.commit()

    client.post("/api/v1/auth/login", json={
        "email": "admin_notif@test.com", "password": "Admin1234"
    })
    token = _extract_token_from_cookies(client)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def recepcionista_headers(client, app):
    with app.app_context():
        u = Usuario(
            nombre="Recepcionista", apellido="Notif",
            email="recep_notif@test.com", rol=RolEnum.recepcionista
        )
        u.password = "Recep1234"
        db.session.add(u)
        db.session.commit()

    client.post("/api/v1/auth/login", json={
        "email": "recep_notif@test.com", "password": "Recep1234"
    })
    token = _extract_token_from_cookies(client)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def cliente_headers(client, app):
    with app.app_context():
        u = Usuario(
            nombre="Cliente", apellido="Notif",
            email="cli_notif@test.com", rol=RolEnum.cliente
        )
        u.password = "Cli1234"
        db.session.add(u)
        db.session.commit()

    client.post("/api/v1/auth/login", json={
        "email": "cli_notif@test.com", "password": "Cli1234"
    })
    token = _extract_token_from_cookies(client)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reserva_en_db(app, request):
    with app.app_context():
        u = Usuario(
            nombre="Huesped", apellido="Notif",
            email=f"huesped_notif_{id(request)}@test.com", rol=RolEnum.cliente
        )
        u.password = "Pass1234"
        db.session.add(u)
        db.session.flush()

        h = Huesped(id_usuario=u.id, documento_id="11111111")
        db.session.add(h)
        db.session.flush()

        hab = Habitacion(
            numero="N01", tipo=TipoHabitacion.simple,
            precio_noche=100000, capacidad=1, piso=1,
            estado=EstadoHabitacion.disponible
        )
        db.session.add(hab)
        db.session.commit()

        fecha_entrada = date.today() + timedelta(days=1)
        fecha_salida = date.today() + timedelta(days=3)

        r = Reserva(
            id_huesped=h.id, id_habitacion=hab.id,
            fecha_entrada=fecha_entrada, fecha_salida=fecha_salida,
            noches=2, subtotal=200000, impuestos=38000, total=238000,
            estado=EstadoReserva.confirmada
        )
        db.session.add(r)
        db.session.commit()
        yield r.id


class TestCrearNotificacion:

    def test_crear_valida(self, client, admin_headers, reserva_en_db):
        resp = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Reserva confirmada exitosamente."
        }, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["tipo"] == "ConfirmacionReserva"
        assert data["data"]["id_reserva"] == reserva_en_db

    def test_crear_campos_obligatorios(self, client, admin_headers):
        resp = client.post("/api/v1/notificaciones", json={}, headers=admin_headers)
        assert resp.status_code == 400

    def test_crear_sin_token(self, client, reserva_en_db):
        resp = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Test"
        })
        assert resp.status_code == 401

    def test_crear_como_cliente_retorna_403(self, client, cliente_headers, reserva_en_db):
        resp = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Test"
        }, headers=cliente_headers)
        assert resp.status_code == 403

    def test_crear_tipo_invalido(self, client, admin_headers, reserva_en_db):
        resp = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "TipoInexistente",
            "mensaje": "Test"
        }, headers=admin_headers)
        assert resp.status_code == 400

    def test_crear_reserva_inexistente(self, client, admin_headers):
        resp = client.post("/api/v1/notificaciones", json={
            "id_reserva": 99999,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Test"
        }, headers=admin_headers)
        assert resp.status_code == 400

    def test_crear_sin_mensaje(self, client, admin_headers, reserva_en_db):
        resp = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva"
        }, headers=admin_headers)
        assert resp.status_code == 400

    def test_crear_como_recepcionista(self, client, recepcionista_headers, reserva_en_db):
        resp = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Test recep"
        }, headers=recepcionista_headers)
        assert resp.status_code == 201


class TestListarNotificaciones:

    def test_listar_vacio(self, client, admin_headers):
        resp = client.get("/api/v1/notificaciones", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["total"] == 0

    def test_listar_con_datos(self, client, admin_headers, reserva_en_db):
        client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Test"
        }, headers=admin_headers)

        resp = client.get("/api/v1/notificaciones", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] == 1

    def test_listar_filtro_tipo(self, client, admin_headers, reserva_en_db):
        client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Confirmación"
        }, headers=admin_headers)
        client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "Recordatorio",
            "mensaje": "Recordatorio"
        }, headers=admin_headers)

        resp = client.get("/api/v1/notificaciones?tipo=ConfirmacionReserva", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] == 1

    def test_listar_filtro_invalido_retorna_400(self, client, admin_headers):
        resp = client.get("/api/v1/notificaciones?tipo=Inexistente", headers=admin_headers)
        assert resp.status_code == 400

    def test_listar_sin_token(self, client):
        resp = client.get("/api/v1/notificaciones")
        assert resp.status_code == 401

    def test_listar_como_cliente_retorna_403(self, client, cliente_headers):
        resp = client.get("/api/v1/notificaciones", headers=cliente_headers)
        assert resp.status_code == 403

    def test_listar_filtro_enviado(self, client, admin_headers, reserva_en_db):
        client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Enviada"
        }, headers=admin_headers)

        resp = client.get("/api/v1/notificaciones?enviado=false", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["total"] >= 1

    def test_listar_filtro_fecha(self, client, admin_headers, reserva_en_db):
        client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Fecha test"
        }, headers=admin_headers)

        ayer = (date.today() - timedelta(days=1)).isoformat()
        manana = (date.today() + timedelta(days=1)).isoformat()
        resp = client.get(
            f"/api/v1/notificaciones?fecha_desde={ayer}&fecha_hasta={manana}",
            headers=admin_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["total"] >= 1


class TestObtenerNotificacion:

    def test_obtener_por_id(self, client, admin_headers, reserva_en_db):
        resp_crear = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Mensaje de prueba"
        }, headers=admin_headers)
        nid = resp_crear.get_json()["data"]["id"]

        resp = client.get(f"/api/v1/notificaciones/{nid}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["mensaje"] == "Mensaje de prueba"

    def test_obtener_inexistente(self, client, admin_headers):
        resp = client.get("/api/v1/notificaciones/99999", headers=admin_headers)
        assert resp.status_code == 404


class TestListarPorReserva:

    def test_listar_por_reserva(self, client, admin_headers, reserva_en_db):
        client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "Factura",
            "mensaje": "Factura generada"
        }, headers=admin_headers)

        resp = client.get(f"/api/v1/notificaciones/reserva/{reserva_en_db}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] == 1

    def test_listar_por_reserva_inexistente(self, client, admin_headers):
        resp = client.get("/api/v1/notificaciones/reserva/99999", headers=admin_headers)
        assert resp.status_code == 404


class TestBuscarNotificaciones:

    def test_buscar_por_mensaje(self, client, admin_headers, reserva_en_db):
        client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "Cancelacion",
            "mensaje": "Reserva cancelada por el cliente"
        }, headers=admin_headers)

        resp = client.get("/api/v1/notificaciones/buscar?q=cancelada", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] == 1

    def test_buscar_sin_query(self, client, admin_headers):
        resp = client.get("/api/v1/notificaciones/buscar", headers=admin_headers)
        assert resp.status_code == 400

    def test_buscar_sin_resultados(self, client, admin_headers):
        resp = client.get("/api/v1/notificaciones/buscar?q=xyzxyzxyz", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] == 0


class TestActualizarNotificacion:

    def test_actualizar_mensaje(self, client, admin_headers, reserva_en_db):
        resp_crear = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Original"
        }, headers=admin_headers)
        nid = resp_crear.get_json()["data"]["id"]

        resp = client.put(f"/api/v1/notificaciones/{nid}", json={
            "mensaje": "Actualizado"
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["mensaje"] == "Actualizado"

    def test_actualizar_enviado_asigna_fecha(self, client, admin_headers, reserva_en_db):
        resp_crear = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Test"
        }, headers=admin_headers)
        nid = resp_crear.get_json()["data"]["id"]

        resp = client.put(f"/api/v1/notificaciones/{nid}", json={
            "enviado": True
        }, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["enviado"] is True
        assert data["fecha_envio"] is not None

    def test_actualizar_sin_campos_validos(self, client, admin_headers, reserva_en_db):
        resp_crear = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Test"
        }, headers=admin_headers)
        nid = resp_crear.get_json()["data"]["id"]

        resp = client.put(f"/api/v1/notificaciones/{nid}", json={
            "campo_invalido": "valor"
        }, headers=admin_headers)
        assert resp.status_code == 400

    def test_actualizar_inexistente(self, client, admin_headers):
        resp = client.put("/api/v1/notificaciones/99999", json={
            "mensaje": "Nuevo"
        }, headers=admin_headers)
        assert resp.status_code == 404

    def test_actualizar_como_recepcionista(self, client, recepcionista_headers, reserva_en_db):
        resp_crear = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Original"
        }, headers=recepcionista_headers)
        nid = resp_crear.get_json()["data"]["id"]

        resp = client.put(f"/api/v1/notificaciones/{nid}", json={
            "mensaje": "Actualizado por recep"
        }, headers=recepcionista_headers)
        assert resp.status_code == 200

    def test_actualizar_tipo(self, client, admin_headers, reserva_en_db):
        resp_crear = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Cambiar tipo"
        }, headers=admin_headers)
        nid = resp_crear.get_json()["data"]["id"]

        resp = client.put(f"/api/v1/notificaciones/{nid}", json={
            "tipo": "Recordatorio"
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["tipo"] == "Recordatorio"


class TestEliminarNotificacion:

    def test_eliminar_valida(self, client, admin_headers, reserva_en_db):
        resp_crear = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "A eliminar"
        }, headers=admin_headers)
        nid = resp_crear.get_json()["data"]["id"]

        resp = client.delete(f"/api/v1/notificaciones/{nid}", headers=admin_headers)
        assert resp.status_code == 200

        resp_get = client.get(f"/api/v1/notificaciones/{nid}", headers=admin_headers)
        assert resp_get.status_code == 404

    def test_eliminar_solo_admin(self, client, recepcionista_headers, admin_headers, reserva_en_db):
        resp_crear = client.post("/api/v1/notificaciones", json={
            "id_reserva": reserva_en_db,
            "tipo": "ConfirmacionReserva",
            "mensaje": "Test"
        }, headers=admin_headers)
        nid = resp_crear.get_json()["data"]["id"]

        resp = client.delete(f"/api/v1/notificaciones/{nid}", headers=recepcionista_headers)
        assert resp.status_code == 403

    def test_eliminar_inexistente(self, client, admin_headers):
        resp = client.delete("/api/v1/notificaciones/99999", headers=admin_headers)
        assert resp.status_code == 404

    def test_eliminar_sin_token(self, client, reserva_en_db):
        resp = client.delete(f"/api/v1/notificaciones/1")
        assert resp.status_code == 401
