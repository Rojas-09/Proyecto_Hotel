"""
Tests del Módulo Reservas - HotelBook Pro
Ejecutar: pytest tests/test_reservas.py -v
"""

import pytest
from datetime import date, timedelta

from app.models.habitacion import (
    EstadoHabitacion,
    Habitacion,
    TipoHabitacion
)
from app.models.usuario import Usuario, RolEnum
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app import db


@pytest.fixture
def habitacion_disponible(app):
    """Habitación disponible para pruebas."""
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
        hid = h.id

    yield {"id": hid, "numero": "201", "precio_noche": 200000}

    with app.app_context():
        db.session.query(Habitacion).delete()
        db.session.commit()


@pytest.fixture
def habitacion_ocupada(app):
    """Habitación ocupada para pruebas."""
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
    """Crea un usuario cliente con Huesped asociado."""
    email = f"cliente_res_{id(request)}@test.com"
    huesped_id = None

    with app.app_context():
        u = Usuario(
            nombre="Cliente",
            apellido="Test",
            email=email,
            rol="cliente"
        )
        u.password = "Cliente1234"
        db.session.add(u)
        db.session.flush()

        h = Huesped(
            id_usuario=u.id,
            documento_id="10203040",
            tipo_documento="CC"
        )
        db.session.add(h)
        db.session.commit()
        huesped_id = h.id

    resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Cliente1234"
    })
    token = resp.get_json()["data"]["token"]
    return {
        "Authorization": f"Bearer {token}"
    }, huesped_id


@pytest.fixture
def admin_user(client, app, request):
    """Crea un usuario admin."""
    email = f"admin_res_{id(request)}@test.com"

    with app.app_context():
        u = Usuario(
            nombre="Admin",
            apellido="Res",
            email=email,
            rol=RolEnum.admin
        )
        u.password = "Admin1234"
        db.session.add(u)
        db.session.commit()

    resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Admin1234"
    })
    token = resp.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def reserva_data():
    """Datos básicos para crear reserva."""
    fecha_entrada = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    fecha_salida = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
    return {
        "id_habitacion": 1,
        "fecha_entrada": fecha_entrada,
        "fecha_salida": fecha_salida,
    }


class TestCrearReserva:

    def test_crear_reserva_valida_como_cliente(
        self,
        client,
        cliente_user,
        habitacion_disponible,
        reserva_data
    ):
        """Crear reserva válida como cliente."""
        headers, huesped_id = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp = client.post(
            "/api/v1/reservas/",
            json=reserva_data,
            headers=headers
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["estado"] == "Pendiente"
        assert data["data"]["id_huesped"] == huesped_id

    def test_crear_reserva_sin_token(
        self,
        client,
        habitacion_disponible,
        reserva_data
    ):
        """Crear reserva sin token falla con 401."""
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp = client.post("/api/v1/reservas/", json=reserva_data)
        assert resp.status_code == 401

    def test_fecha_entrada_en_pasado(
        self,
        client,
        cliente_user,
        habitacion_disponible
    ):
        """Fecha de entrada en el pasado falla con 400."""
        headers, _ = cliente_user
        fecha_entrada = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
        fecha_salida = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
        resp = client.post(
            "/api/v1/reservas/",
            json={
                "id_habitacion": habitacion_disponible["id"],
                "fecha_entrada": fecha_entrada,
                "fecha_salida": fecha_salida,
            },
            headers=headers
        )
        assert resp.status_code == 400

    def test_fecha_entrada_igual_salida(
        self,
        client,
        cliente_user,
        habitacion_disponible
    ):
        """Fecha entrada >= salida falla con 400."""
        headers, _ = cliente_user
        fecha = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        resp = client.post(
            "/api/v1/reservas/",
            json={
                "id_habitacion": habitacion_disponible["id"],
                "fecha_entrada": fecha,
                "fecha_salida": fecha,
            },
            headers=headers
        )
        assert resp.status_code == 400

    def test_habitacion_inexistente(self, client, cliente_user, reserva_data):
        """Habitación inexistente falla con 404."""
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = 9999
        resp = client.post(
            "/api/v1/reservas/",
            json=reserva_data,
            headers=headers
        )
        assert resp.status_code == 404

    def test_habitacion_ocupada(
        self,
        client,
        cliente_user,
        habitacion_ocupada,
        reserva_data
    ):
        """Habitación ocupada falla con 400."""
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_ocupada["id"]
        resp = client.post(
            "/api/v1/reservas/",
            json=reserva_data,
            headers=headers
        )
        assert resp.status_code == 400


class TestObtenerReservas:

    def test_mis_reservas_como_cliente(
        self,
        client,
        cliente_user,
        habitacion_disponible,
        reserva_data
    ):
        """Cliente obtiene sus reservas."""
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        client.post("/api/v1/reservas/", json=reserva_data, headers=headers)

        resp = client.get("/api/v1/reservas/mis-reservas", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_obtener_todas_como_admin(
        self,
        client,
        admin_user,
        habitacion_disponible,
        cliente_user,
        reserva_data
    ):
        """Admin obtiene todas las reservas."""
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        client.post("/api/v1/reservas/", json=reserva_data, headers=headers_cliente)

        resp = client.get("/api/v1/reservas/", headers=admin_user)
        assert resp.status_code == 200
        assert resp.get_json()["total"] >= 1

    def test_obtener_todas_como_cliente_retorna_403(self, client, cliente_user):
        """Cliente no puede obtener todas las reservas."""
        headers, _ = cliente_user
        resp = client.get("/api/v1/reservas/", headers=headers)
        assert resp.status_code == 403


class TestFlujoReserva:

    def test_confirmar_reserva_pendiente(
        self,
        client,
        admin_user,
        habitacion_disponible,
        cliente_user,
        reserva_data
    ):
        """Confirmar reserva en estado Pendiente."""
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/",
            json=reserva_data,
            headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/confirmar",
            headers=admin_user
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Confirmada"

    def test_confirmar_reserva_ya_confirmada(
        self,
        client,
        admin_user,
        habitacion_disponible,
        cliente_user,
        reserva_data
    ):
        """Confirmar reserva ya confirmada falla con 400."""
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/",
            json=reserva_data,
            headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(
            f"/api/v1/reservas/{reserva_id}/confirmar",
            headers=admin_user
        )

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/confirmar",
            headers=admin_user
        )
        assert resp.status_code == 400

    def test_cancelar_con_motivo(
        self,
        client,
        cliente_user,
        habitacion_disponible,
        reserva_data
    ):
        """Cancelar reserva con motivo."""
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/",
            json=reserva_data,
            headers=headers
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/cancelar",
            json={"motivo": "Cambio de planes"},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Cancelada"

    def test_checkin_de_reserva_confirmada(
        self,
        client,
        admin_user,
        habitacion_disponible,
        cliente_user,
        reserva_data
    ):
        """Check-in de reserva confirmada."""
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/",
            json=reserva_data,
            headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(
            f"/api/v1/reservas/{reserva_id}/confirmar",
            headers=admin_user
        )

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/checkin",
            headers=admin_user
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Ocupada"

    def test_checkout_de_reserva_ocupada(
        self,
        client,
        admin_user,
        habitacion_disponible,
        cliente_user,
        reserva_data,
        app
    ):
        """Check-out de reserva ocupada."""
        from decimal import Decimal

        headers_cliente, huesped_id = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/",
            json=reserva_data,
            headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(
            f"/api/v1/reservas/{reserva_id}/confirmar",
            headers=admin_user
        )
        client.put(
            f"/api/v1/reservas/{reserva_id}/checkin",
            headers=admin_user
        )

        with app.app_context():
            from app.models.reserva import Reserva
            reserva = Reserva.query.get(reserva_id)
            monto_garantia = (Decimal(str(reserva.total)) * Decimal("0.50")).quantize(Decimal("0.01"))
            pago_garantia = Pago(
                id_reserva=reserva_id,
                monto=monto_garantia,
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(pago_garantia)
            pago_liq = Pago(
                id_reserva=reserva_id,
                monto=Decimal(str(reserva.total)) * Decimal("0.50"),
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.liquidacion,
                estado=EstadoPago.aprobado,
            )
            db.session.add(pago_liq)
            db.session.commit()

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/checkout",
            headers=admin_user
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Completada"

    def test_checkout_sin_checkin_previo(
        self,
        client,
        admin_user,
        habitacion_disponible,
        cliente_user,
        reserva_data
    ):
        """Check-out sin check-in previo falla con 400."""
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/",
            json=reserva_data,
            headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(
            f"/api/v1/reservas/{reserva_id}/confirmar",
            headers=admin_user
        )

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/checkout",
            headers=admin_user
        )
        assert resp.status_code == 400