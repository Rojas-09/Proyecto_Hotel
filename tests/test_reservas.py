"""
Tests del Módulo Reservas - HotelBook Pro
Ejecutar: pytest tests/test_reservas.py -v
"""

import pytest
from tests.conftest import _extract_token_from_cookies
from datetime import date, timedelta

from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
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
        u = Usuario(nombre="Cliente", apellido="Test", email=email, rol="cliente")
        u.password = "Cliente1234"
        db.session.add(u)
        db.session.flush()

        h = Huesped(id_usuario=u.id, documento_id="10203040", tipo_documento="CC")
        db.session.add(h)
        db.session.commit()
        huesped_id = h.id

    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Cliente1234"}
    )
    token = _extract_token_from_cookies(client)
    return {"Authorization": f"Bearer {token}"}, huesped_id


@pytest.fixture
def admin_user(client, app, request):
    """Crea un usuario admin."""
    email = f"admin_res_{id(request)}@test.com"

    with app.app_context():
        u = Usuario(nombre="Admin", apellido="Res", email=email, rol=RolEnum.admin)
        u.password = "Admin1234"
        db.session.add(u)
        db.session.commit()

    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Admin1234"}
    )
    token = _extract_token_from_cookies(client)
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
        self, client, cliente_user, habitacion_disponible, reserva_data
    ):
        """Crear reserva válida como cliente."""
        headers, huesped_id = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp = client.post("/api/v1/reservas/", json=reserva_data, headers=headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["estado"] == "Pendiente"
        assert data["data"]["id_huesped"] == huesped_id

    def test_crear_reserva_sin_token(self, client, habitacion_disponible, reserva_data):
        """Crear reserva sin token falla con 401."""
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp = client.post("/api/v1/reservas/", json=reserva_data)
        assert resp.status_code == 401

    def test_fecha_entrada_en_pasado(self, client, cliente_user, habitacion_disponible):
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
            headers=headers,
        )
        assert resp.status_code == 400

    def test_fecha_entrada_igual_salida(
        self, client, cliente_user, habitacion_disponible
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
            headers=headers,
        )
        assert resp.status_code == 400

    def test_habitacion_inexistente(self, client, cliente_user, reserva_data):
        """Habitación inexistente falla con 404."""
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = 9999
        resp = client.post("/api/v1/reservas/", json=reserva_data, headers=headers)
        assert resp.status_code == 404

    def test_habitacion_ocupada(
        self, client, cliente_user, habitacion_ocupada, reserva_data
    ):
        """Habitación ocupada falla con 400."""
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_ocupada["id"]
        resp = client.post("/api/v1/reservas/", json=reserva_data, headers=headers)
        assert resp.status_code == 400


class TestObtenerReservas:

    def test_mis_reservas_como_cliente(
        self, client, cliente_user, habitacion_disponible, reserva_data
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
        self, client, admin_user, habitacion_disponible, cliente_user, reserva_data
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
        self, client, admin_user, habitacion_disponible, cliente_user, reserva_data
    ):
        """Confirmar reserva en estado Pendiente."""
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Confirmada"

    def test_confirmar_reserva_ya_confirmada(
        self, client, admin_user, habitacion_disponible, cliente_user, reserva_data
    ):
        """Confirmar reserva ya confirmada falla con 400."""
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user
        )
        assert resp.status_code == 400

    def test_cancelar_con_motivo(
        self, client, cliente_user, habitacion_disponible, reserva_data
    ):
        """Cancelar reserva con motivo."""
        headers, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.put(
            f"/api/v1/reservas/{reserva_id}/cancelar",
            json={"motivo": "Cambio de planes"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Cancelada"

    def test_checkin_de_reserva_confirmada(
        self, client, admin_user, habitacion_disponible, cliente_user, reserva_data
    ):
        """Check-in de reserva confirmada."""
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)

        resp = client.put(f"/api/v1/reservas/{reserva_id}/checkin", headers=admin_user)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"].lower() == "ocupada"

    def test_checkout_de_reserva_ocupada(
        self, client, admin_user, habitacion_disponible, cliente_user, reserva_data, app
    ):
        """Check-out de reserva ocupada."""
        from decimal import Decimal

        headers_cliente, huesped_id = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)
        client.put(f"/api/v1/reservas/{reserva_id}/checkin", headers=admin_user)

        with app.app_context():
            from app.models.reserva import Reserva

            reserva = db.session.get(Reserva, reserva_id)
            monto_garantia = (Decimal(str(reserva.total)) * Decimal("0.50")).quantize(
                Decimal("0.01")
            )
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

        resp = client.put(f"/api/v1/reservas/{reserva_id}/checkout", headers=admin_user)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["estado"] == "Completada"

    def test_checkout_sin_checkin_previo(
        self, client, admin_user, habitacion_disponible, cliente_user, reserva_data
    ):
        """Check-out sin check-in previo falla con 400."""
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        client.put(f"/api/v1/reservas/{reserva_id}/confirmar", headers=admin_user)

        resp = client.put(f"/api/v1/reservas/{reserva_id}/checkout", headers=admin_user)
        assert resp.status_code == 400


class TestEliminarReserva:

    def test_eliminar_como_admin(
        self, client, admin_user, cliente_user, habitacion_disponible, reserva_data
    ):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.delete(f"/api/v1/reservas/{reserva_id}", headers=admin_user)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["mensaje"] == "Reserva eliminada permanentemente."
        # Verificar que la reserva ya no existe
        resp_get = client.get(f"/api/v1/reservas/{reserva_id}", headers=admin_user)
        assert resp_get.status_code == 404

    def test_eliminar_inexistente(self, client, admin_user):
        resp = client.delete("/api/v1/reservas/99999", headers=admin_user)
        assert resp.status_code == 404

    def test_eliminar_sin_token(self, client):
        resp = client.delete("/api/v1/reservas/1")
        assert resp.status_code == 401

    def test_eliminar_como_cliente_retorna_403(
        self, client, cliente_user, habitacion_disponible, reserva_data
    ):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.delete(f"/api/v1/reservas/{reserva_id}", headers=headers_cliente)
        assert resp.status_code == 403

    def test_eliminar_con_motivo(
        self, client, admin_user, cliente_user, habitacion_disponible, reserva_data
    ):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.delete(
            f"/api/v1/reservas/{reserva_id}",
            json={"motivo": "Reserva duplicada"},
            headers=admin_user,
        )
        assert resp.status_code == 200


class TestActualizarReserva:

    def test_actualizar_fechas_como_admin(
        self, client, admin_user, cliente_user, habitacion_disponible, reserva_data
    ):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        from datetime import date, timedelta

        nuevas_fechas = {
            "fecha_entrada": (date.today() + timedelta(days=6)).strftime("%Y-%m-%d"),
            "fecha_salida": (date.today() + timedelta(days=9)).strftime("%Y-%m-%d"),
        }
        resp = client.patch(
            f"/api/v1/reservas/{reserva_id}", json=nuevas_fechas, headers=admin_user
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["fecha_entrada"] == nuevas_fechas["fecha_entrada"]
        assert data["noches"] == 3
        assert data["subtotal"] == 600000.0
        assert data["impuestos"] == 114000.0
        assert data["total"] == 714000.0

    def test_actualizar_habitacion_recalcula_totales(
        self, client, admin_user, cliente_user, habitacion_disponible, app
    ):
        headers_cliente, _ = cliente_user
        fecha_entrada = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        fecha_salida = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

        resp_crear = client.post(
            "/api/v1/reservas/",
            json={
                "id_habitacion": habitacion_disponible["id"],
                "fecha_entrada": fecha_entrada,
                "fecha_salida": fecha_salida,
            },
            headers=headers_cliente,
        )
        assert resp_crear.status_code == 201
        reserva_id = resp_crear.get_json()["data"]["id"]
        data_original = resp_crear.get_json()["data"]
        assert data_original["subtotal"] == 400000.0

        with app.app_context():
            hab_b = Habitacion(
                numero="301",
                tipo=TipoHabitacion.suite,
                descripcion="Suite de lujo",
                precio_noche=300000,
                capacidad=2,
                piso=3,
                estado=EstadoHabitacion.disponible,
            )
            db.session.add(hab_b)
            db.session.commit()
            hab_b_id = hab_b.id

        resp = client.patch(
            f"/api/v1/reservas/{reserva_id}",
            json={"id_habitacion": hab_b_id},
            headers=admin_user,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["id_habitacion"] == hab_b_id
        assert data["noches"] == 2
        assert data["subtotal"] == 600000.0
        assert data["impuestos"] == 114000.0
        assert data["total"] == 714000.0

    def test_actualizar_habitacion_y_fechas_recalcula_totales(
        self, client, admin_user, cliente_user, habitacion_disponible, app
    ):
        headers_cliente, _ = cliente_user
        fecha_entrada = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        fecha_salida = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")

        resp_crear = client.post(
            "/api/v1/reservas/",
            json={
                "id_habitacion": habitacion_disponible["id"],
                "fecha_entrada": fecha_entrada,
                "fecha_salida": fecha_salida,
            },
            headers=headers_cliente,
        )
        assert resp_crear.status_code == 201
        reserva_id = resp_crear.get_json()["data"]["id"]

        with app.app_context():
            hab_c = Habitacion(
                numero="302",
                tipo=TipoHabitacion.suite,
                descripcion="Suite premium",
                precio_noche=350000,
                capacidad=2,
                piso=3,
                estado=EstadoHabitacion.disponible,
            )
            db.session.add(hab_c)
            db.session.commit()
            hab_c_id = hab_c.id

        nuevas_fechas_y_hab = {
            "id_habitacion": hab_c_id,
            "fecha_entrada": (date.today() + timedelta(days=6)).strftime("%Y-%m-%d"),
            "fecha_salida": (date.today() + timedelta(days=10)).strftime("%Y-%m-%d"),
        }
        resp = client.patch(
            f"/api/v1/reservas/{reserva_id}",
            json=nuevas_fechas_y_hab,
            headers=admin_user,
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["noches"] == 4
        assert data["subtotal"] == 1400000.0
        assert data["impuestos"] == 266000.0
        assert data["total"] == 1666000.0

    def test_actualizar_como_cliente_su_reserva(
        self, client, cliente_user, habitacion_disponible, reserva_data
    ):
        headers_cliente, huesped_id = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.patch(
            f"/api/v1/reservas/{reserva_id}",
            json={
                "fecha_entrada": reserva_data["fecha_entrada"],
                "fecha_salida": (
                    date.fromisoformat(reserva_data["fecha_salida"]) + timedelta(days=1)
                ).strftime("%Y-%m-%d"),
            },
            headers=headers_cliente,
        )
        assert resp.status_code == 200

    def test_actualizar_body_vacio(
        self, client, admin_user, cliente_user, habitacion_disponible, reserva_data
    ):
        headers_cliente, _ = cliente_user
        reserva_data["id_habitacion"] = habitacion_disponible["id"]
        resp_crear = client.post(
            "/api/v1/reservas/", json=reserva_data, headers=headers_cliente
        )
        reserva_id = resp_crear.get_json()["data"]["id"]

        resp = client.patch(
            f"/api/v1/reservas/{reserva_id}", json={}, headers=admin_user
        )
        assert resp.status_code == 400

    def test_actualizar_inexistente(self, client, admin_user):
        resp = client.patch(
            "/api/v1/reservas/99999",
            json={"fecha_entrada": "2026-12-01"},
            headers=admin_user,
        )
        assert resp.status_code == 404

    def test_actualizar_sin_token(self, client):
        resp = client.patch("/api/v1/reservas/1", json={"fecha_entrada": "2026-12-01"})
        assert resp.status_code == 401
