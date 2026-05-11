"""
Tests del Módulo Reservas - HotelBook Pro
Ejecutar: pytest tests/test_reservas.py -v
"""

import pytest
from datetime import date, timedelta

from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.reserva import EstadoReserva, Reserva
from app.models.usuario import Usuario
from app import db


@pytest.fixture
def habitacion_disponible(app):
    with app.app_context():
        h = Habitacion(
            numero="201",
            tipo=TipoHabitacion.doble,
            descripcion="Habitacion doble",
            precio_noche=200000,
            capacidad=2,
            piso=2,
            estado=EstadoHabitacion.disponible,
        )
        db.session.add(h)
        db.session.commit()
        yield h.to_dict()
        db.session.query(Habitacion).delete()
        db.session.commit()


@pytest.fixture
def habitacion_ocupada(app):
    with app.app_context():
        h = Habitacion(
            numero="202",
            tipo=TipoHabitacion.simple,
            descripcion="Habitacion simple",
            precio_noche=150000,
            capacidad=1,
            piso=2,
            estado=EstadoHabitacion.ocupada,
        )
        db.session.add(h)
        db.session.commit()
        yield h.to_dict()
        db.session.query(Habitacion).delete()
        db.session.commit()


@pytest.fixture
def cliente_user(client, app, request):
    """Crea un usuario cliente con email único por test."""
    email = f"cliente_{id(request)}@test.com"
    user_id = None
    with app.app_context():
        u = Usuario(nombre="Cliente", apellido="Test", email=email, rol="cliente")
        u.password = "Cliente1234"
        db.session.add(u)
        db.session.commit()
        user_id = u.id
    resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Cliente1234"
    })
    token = resp.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}, user_id


@pytest.fixture
def admin_user(client, app, request):
    """Crea un usuario admin con email único por test."""
    email = f"admin_{id(request)}@test.com"
    # Crear primer admin si es posible
    resp = client.post("/api/v1/auth/register-admin", json={
        "nombre": "Admin",
        "apellido": "Res",
        "email": email,
        "password": "Admin1234",
    })
    
    # Si ya existe admin, crear como cliente y cambiar a admin en BD
    if resp.status_code != 201:
        client.post("/api/v1/auth/register", json={
            "nombre": "Admin",
            "apellido": "Res",
            "email": email,
            "password": "Admin1234",
        })
        with app.app_context():
            u = Usuario.query.filter_by(email=email).first()
            if u:
                u.rol = "admin"
                db.session.commit()
    
    resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Admin1234"
    })
    token = resp.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reserva_data():
    fecha_entrada = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    fecha_salida = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
    return {
        "id_habitacion": 1,
        "fecha_entrada": fecha_entrada,
        "fecha_salida": fecha_salida,
    }


class TestCrearReserva:

    def test_crear_reserva_valida_como_cliente(self, client, cliente_user, habitacion_disponible, reserva_data):
        headers, cliente_id = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp = client.post("/api/v1/reservas/", json=reserva_data, headers=headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["estado"] == "Pendiente"

    def test_crear_reserva_sin_token(self, client, habitacion_disponible, reserva_data):
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp = client.post("/api/v1/reservas/", json=reserva_data)
        assert resp.status_code == 401

    def test_fecha_entrada_en_pasado(self, client, cliente_user, habitacion_disponible):
        headers, _ = cliente_user
        fecha_entrada = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
        fecha_salida = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
        resp = client.post("/api/v1/reservas/", json={
            "id_habitacion": habitacion_disponible["id"],
            "fecha_entrada": fecha_entrada,
            "fecha_salida": fecha_salida,
        }, headers=headers)
        assert resp.status_code == 400

    def test_fecha_entrada_mayor_igual_salida(self, client, cliente_user, habitacion_disponible):
        headers, _ = cliente_user
        fecha = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        resp = client.post("/api/v1/reservas/", json={
            "id_habitacion": habitacion_disponible["id"],
            "fecha_entrada": fecha,
            "fecha_salida": fecha,
        }, headers=headers)
        assert resp.status_code == 400

    def test_habitacion_inexistente(self, client, cliente_user):
        headers, _ = cliente_user
        resp = client.post("/api/v1/reservas/", json={
            "id_habitacion": 99999,
            "fecha_entrada": "2027-06-01",
            "fecha_salida": "2027-06-03",
        }, headers=headers)
        assert resp.status_code == 404

    def test_habitacion_ocupada(self, client, cliente_user, habitacion_ocupada):
        headers, _ = cliente_user
        resp = client.post("/api/v1/reservas/", json={
            "id_habitacion": habitacion_ocupada["id"],
            "fecha_entrada": "2027-06-01",
            "fecha_salida": "2027-06-03",
        }, headers=headers)
        assert resp.status_code == 400


class TestObtenerReservas:

    def test_mis_reservas_como_cliente(self, client, cliente_user, habitacion_disponible, reserva_data):
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        client.post("/api/v1/reservas/", json=reserva_data, headers=headers)

        resp = client.get("/api/v1/reservas/mis-reservas", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert "cliente_email" in data["data"][0]

    def test_obtener_todas_como_admin(self, client, admin_user, habitacion_disponible, cliente_user, reserva_data):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        client.post("/api/v1/reservas/", json=reserva_data, headers=headers_cliente)

        resp = client.get("/api/v1/reservas/", headers=admin_user)
        assert resp.status_code == 200
        assert resp.get_json()["total"] >= 1

    def test_obtener_todas_como_cliente_retorna_403(self, client, cliente_user):
        headers, _ = cliente_user
        resp = client.get("/api/v1/reservas/", headers=headers)
        assert resp.status_code == 403

    def test_obtener_reserva_propia_como_cliente(self, client, cliente_user, habitacion_disponible, reserva_data):
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post("/api/v1/reservas/", json=reserva_data, headers=headers)
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.get(f"/api/v1/reservas/{reserva_id}", headers=headers)
        assert resp.status_code == 200

    def test_obtener_reserva_ajena_como_cliente_retorna_403(self, client, cliente_user, admin_user, habitacion_disponible, reserva_data):
        headers_admin = admin_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post("/api/v1/reservas/", json=reserva_data, headers=headers_admin)
        reserva_id = resp_crear.get_json()["data"]["id"]

        headers_cliente, _ = cliente_user
        resp = client.get(f"/api/v1/reservas/{reserva_id}", headers=headers_cliente)
        assert resp.status_code == 403


class TestFlujoReserva:

    def test_confirmar_reserva_pendiente(self, client, admin_user, habitacion_disponible, cliente_user, reserva_data):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post("/api/v1/reservas/", json=reserva_data, headers=headers_cliente)
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Confirmada"

    def test_confirmar_reserva_ya_confirmada(self, client, admin_user, habitacion_disponible, cliente_user, reserva_data):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post("/api/v1/reservas/", json=reserva_data, headers=headers_cliente)
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)

        resp = client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)
        assert resp.status_code == 400

    def test_cancelar_con_motivo(self, client, cliente_user, habitacion_disponible, reserva_data):
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post("/api/v1/reservas/", json=reserva_data, headers=headers)
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/cancelar",
            json={"motivo": "Cambio de planes"},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Cancelada"

    def test_cancelar_con_menos_de_24h(self, client, app, cliente_user):
        from app.models.habitacion import Habitacion, TipoHabitacion, EstadoHabitacion
        from app.models.usuario import Usuario
        from app.services import reserva_service

        with app.app_context():
            h = Habitacion(
                numero="301",
                tipo=TipoHabitacion.simple,
                precio_noche=150000,
                capacidad=1,
                piso=3,
                estado=EstadoHabitacion.disponible,
            )
            db.session.add(h)
            db.session.commit()
            habitacion_id = h.id

        headers, cliente_id = cliente_user
        fecha_entrada = (date.today() + timedelta(hours=12)).strftime("%Y-%m-%d")
        fecha_salida = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")

        reserva = reserva_service.crear({
            "id_habitacion": habitacion_id,
            "fecha_entrada": fecha_entrada,
            "fecha_salida": fecha_salida,
        }, Usuario.query.get(cliente_id))

        resp = client.put(
            f"/api/v1/reservas/{reserva['id']}/cancelar",
            headers=headers,
            json={},
            content_type="application/json"
        )
        assert resp.status_code == 400
        assert "24 horas" in resp.get_json()["mensaje"]

    def test_checkin_de_reserva_confirmada(self, client, admin_user, habitacion_disponible, cliente_user, reserva_data):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post("/api/v1/reservas/", json=reserva_data, headers=headers_cliente)
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)

        resp = client.put(f"/api/v1/reservas/{reserva_id}/checkin", headers=admin_user)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Ocupada"

    def test_checkout_de_reserva_ocupada(self, client, admin_user, habitacion_disponible, cliente_user, reserva_data):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post("/api/v1/reservas/", json=reserva_data, headers=headers_cliente)
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)
        client.put(f"/api/v1/reservas/{reserva_id}/checkin", headers=admin_user)

        resp = client.put(f"/api/v1/reservas/{reserva_id}/checkout", headers=admin_user)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Completada"

    def test_checkout_sin_checkin_previo(self, client, admin_user, habitacion_disponible, cliente_user, reserva_data):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post("/api/v1/reservas/", json=reserva_data, headers=headers_cliente)
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)

        resp = client.put(f"/api/v1/reservas/{reserva_id}/checkout", headers=admin_user)
        assert resp.status_code == 400