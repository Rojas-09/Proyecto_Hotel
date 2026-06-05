"""
Tests adicionales del controlador de Pagos (RF-13).
Cubre los happy paths y errores 400/404 de todos los endpoints
para llevar el coverage de 86% → 90%+.
"""
from decimal import Decimal

import pytest  # noqa: F401 (used in conftest.py)

from app import db
from app.models.habitacion import Habitacion, TipoHabitacion, EstadoHabitacion
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app.models.reembolso import EstadoReembolso, Reembolso  # noqa: F401 (used in conftest.py)
from app.models.reserva import EstadoReserva, Reserva  # noqa: F401 (used in conftest.py)
from app.models.usuario import RolEnum, Usuario
from app.utils.jwt_helper import generar_token


# ---------------------------------------------------------------------------
# Helpers de fixtures
# ---------------------------------------------------------------------------

def _crear_usuario(rol: RolEnum, sufijo: str) -> Usuario:
    u = Usuario(
        nombre=f"Test",  # noqa: F541 (dynamic name)
        apellido=f"{sufijo}",
        email=f"test_{sufijo}_{id(sufijo)}@hotel.com",  # noqa: F541 (dynamic email)
        rol=rol,
    )
    u.password = "Password123!"
    db.session.add(u)
    db.session.flush()
    return u


def _crear_huesped(usuario: Usuario) -> Huesped:
    h = Huesped(
        id_usuario=usuario.id,
        documento_id=f"CC{hash(str(usuario.id)) % 100000}",
        tipo_documento="CC",
    )
    db.session.add(h)
    db.session.flush()
    return h


def _crear_habitacion() -> Habitacion:
    import random
    hab = Habitacion(
        numero=f"99{random.randint(1, 999):03d}",
        tipo=TipoHabitacion.doble,
        precio_noche=Decimal("100000.00"),
        capacidad=2,
        estado=EstadoHabitacion.disponible,
    )
    db.session.add(hab)
    db.session.flush()
    return hab


def _crear_reserva(huesped: Huesped, habitacion: Habitacion,
                   estado: EstadoReserva = EstadoReserva.pendiente) -> Reserva:
    from datetime import date, timedelta
    hoy = date.today()
    entrada = hoy + timedelta(days=5)
    salida = hoy + timedelta(days=7)
    noches = 2
    subtotal = Decimal("200000.00")
    impuestos = Decimal("38000.00")
    total = Decimal("238000.00")
    reserva = Reserva(
        id_huesped=huesped.id,
        id_habitacion=habitacion.id,
        fecha_entrada=entrada,
        fecha_salida=salida,
        noches=noches,
        subtotal=subtotal,
        impuestos=impuestos,
        total=total,
        estado=estado,
    )
    db.session.add(reserva)
    db.session.flush()
    return reserva


def _pago_garantia(reserva: Reserva) -> Pago:
    monto = (Decimal(str(reserva.total)) * Decimal("0.50")).quantize(Decimal("0.01"))
    p = Pago(
        id_reserva=reserva.id,
        monto=monto,
        metodo=MetodoPago.efectivo,
        tipo=TipoPago.garantia,
        estado=EstadoPago.aprobado,
    )
    db.session.add(p)
    db.session.flush()
    return p


def _pago_liquidacion(reserva: Reserva) -> Pago:
    monto = (Decimal(str(reserva.total)) * Decimal("0.50")).quantize(Decimal("0.01"))
    p = Pago(
        id_reserva=reserva.id,
        monto=monto,
        metodo=MetodoPago.efectivo,
        tipo=TipoPago.liquidacion,
        estado=EstadoPago.aprobado,
    )
    db.session.add(p)
    db.session.flush()
    return p


def _token(usuario: Usuario) -> str:
    rol = usuario.rol.value if hasattr(usuario.rol, "value") else usuario.rol
    return generar_token(usuario.id, usuario.email, rol)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# TestGetPagosReserva — GET /api/v1/pagos/reserva/<id>
# ---------------------------------------------------------------------------

class TestGetPagosReserva:
    """Cubre el endpoint GET que no fue testeado en test_pagos.py."""

    def test_lista_vacia(self, client, app):
        """200 — reserva sin pagos devuelve lista vacía."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_get1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_get1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.get(f"/api/v1/pagos/reserva/{rid}", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []
        assert data["total"] == 0

    def test_lista_con_pagos(self, client, app):
        """200 — devuelve los pagos existentes con total correcto."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_get2")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_get2")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            _pago_garantia(reserva)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.get(f"/api/v1/pagos/reserva/{rid}", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) == 1
        assert data["total"] == 1
        assert data["data"][0]["tipo"] == "Garantia"

    def test_reserva_no_existe(self, client, app):
        """404 — reserva inexistente."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_get3")
            db.session.commit()
            token = _token(admin)

        resp = client.get("/api/v1/pagos/reserva/99999", headers=_auth(token))
        assert resp.status_code == 404

    def test_recepcionista_puede_listar(self, client, app):
        """200 — recepcionista tiene permiso para listar pagos."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_get1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_get4")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab)
            db.session.commit()
            token = _token(recep)
            rid = reserva.id

        resp = client.get(f"/api/v1/pagos/reserva/{rid}", headers=_auth(token))
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TestPostLiquidacionController — POST /api/v1/pagos/liquidacion/<id>
# ---------------------------------------------------------------------------

class TestPostLiquidacionController:
    """Happy path y errores 400/404 del endpoint de liquidación."""

    def test_liquidacion_exitosa(self, client, app):
        """201 — recepcionista cobra liquidación con efectivo."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_liq1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_liq1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            _pago_garantia(reserva)
            db.session.commit()
            token = _token(recep)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/liquidacion/{rid}",
            json={"metodo": "Efectivo"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["tipo"] == "Liquidacion"
        assert data["data"]["estado"] == "Aprobado"

    def test_liquidacion_reserva_no_existe(self, client, app):
        """404 — reserva inexistente."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_liq2")
            db.session.commit()
            token = _token(recep)

        resp = client.post(
            "/api/v1/pagos/liquidacion/99999",
            json={"metodo": "Efectivo"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_liquidacion_sin_garantia_previa(self, client, app):
        """400 — no existe garantía aprobada."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_liq3")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_liq3")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            db.session.commit()
            token = _token(recep)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/liquidacion/{rid}",
            json={"metodo": "Efectivo"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "garantía" in resp.get_json()["mensaje"].lower()

    def test_liquidacion_estado_incorrecto(self, client, app):
        """400 — reserva no está en estado Ocupada."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_liq4")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_liq4")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            # reserva en pendiente, no ocupada
            reserva = _crear_reserva(huesped, hab, EstadoReserva.pendiente)
            db.session.commit()
            token = _token(recep)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/liquidacion/{rid}",
            json={"metodo": "Efectivo"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "ocupada" in resp.get_json()["mensaje"].lower()

    def test_liquidacion_metodo_invalido(self, client, app):
        """400 — método de pago no reconocido."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_liq5")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_liq5")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            _pago_garantia(reserva)
            db.session.commit()
            token = _token(recep)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/liquidacion/{rid}",
            json={"metodo": "Bitcoin"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "inválido" in resp.get_json()["mensaje"].lower()

    def test_liquidacion_duplicada(self, client, app):
        """400 — ya existe una liquidación aprobada."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_liq6")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_liq6")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            _pago_garantia(reserva)
            _pago_liquidacion(reserva)
            db.session.commit()
            token = _token(recep)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/liquidacion/{rid}",
            json={"metodo": "Efectivo"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "liquidación" in resp.get_json()["mensaje"].lower()


# ---------------------------------------------------------------------------
# TestPostReembolsoController — POST /api/v1/pagos/reembolso/<id>
# ---------------------------------------------------------------------------

class TestPostReembolsoController:
    """Happy path y errores 400/404 del endpoint de reembolso."""

    def test_reembolso_exitoso(self, client, app):
        """201 — admin crea reembolso de un pago aprobado."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_rem1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_rem1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            garantia = _pago_garantia(reserva)
            db.session.commit()
            token = _token(admin)
            pid = garantia.id

        resp = client.post(
            f"/api/v1/pagos/reembolso/{pid}",
            json={"motivo": "Cliente canceló por emergencia"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["estado"] == "Procesado"
        assert data["data"]["motivo"] == "Cliente canceló por emergencia"

    def test_reembolso_pago_no_existe(self, client, app):
        """404 — pago inexistente."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_rem2")
            db.session.commit()
            token = _token(admin)

        resp = client.post(
            "/api/v1/pagos/reembolso/99999",
            json={"motivo": "Prueba"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_reembolso_motivo_vacio(self, client, app):
        """400 — motivo en blanco."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_rem3")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_rem3")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            garantia = _pago_garantia(reserva)
            db.session.commit()
            token = _token(admin)
            pid = garantia.id

        resp = client.post(
            f"/api/v1/pagos/reembolso/{pid}",
            json={"motivo": "   "},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "obligatorio" in resp.get_json()["mensaje"].lower()

    def test_reembolso_motivo_ausente(self, client, app):
        """400 — body sin campo motivo."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_rem4")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_rem4")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            garantia = _pago_garantia(reserva)
            db.session.commit()
            token = _token(admin)
            pid = garantia.id

        resp = client.post(
            f"/api/v1/pagos/reembolso/{pid}",
            json={},
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_reembolso_pago_no_aprobado(self, client, app):
        """400 — pago en estado Rechazado no puede reembolsarse."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "rem_no_aprob")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_rem5")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            garantia = _pago_garantia(reserva)
            garantia.estado = EstadoPago.rechazado
            db.session.commit()
            token = _token(admin)
            pid = garantia.id

        resp = client.post(
            f"/api/v1/pagos/reembolso/{pid}",
            json={"motivo": "Prueba"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "aprobados" in resp.get_json()["mensaje"].lower()

    def test_reembolso_duplicado(self, client, app):
        """400 — el pago ya tiene un reembolso asociado."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "rem_dup")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_rem6")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            garantia = _pago_garantia(reserva)
            garantia.estado = EstadoPago.aprobado
            db.session.commit()
            token = _token(admin)
            pid = garantia.id

        client.post(
            f"/api/v1/pagos/reembolso/{pid}",
            json={"motivo": "Primer reembolso"},
            headers=_auth(token),
        )

        resp = client.post(
            f"/api/v1/pagos/reembolso/{pid}",
            json={"motivo": "Segundo intento"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "reembolso" in resp.get_json()["mensaje"].lower()


# ---------------------------------------------------------------------------
# TestPostGarantiaController — rutas de error adicionales
# ---------------------------------------------------------------------------

class TestPostGarantiaController:
    """Cubre errores 400 del endpoint de garantía no cubiertos antes."""

    def test_garantia_metodo_invalido(self, client, app):
        """400 — método de pago desconocido."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_gar1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_gar1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/garantia/{rid}",
            json={"metodo": "Cripto"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "inválido" in resp.get_json()["mensaje"].lower()

    def test_garantia_metodo_ausente(self, client, app):
        """400 — body sin campo metodo."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_gar2")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_gar2")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/garantia/{rid}",
            json={},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "obligatorio" in resp.get_json()["mensaje"].lower()

    def test_garantia_reserva_ya_confirmada(self, client, app):
        """400 — reserva no está en pendiente."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_gar3")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_gar3")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab, EstadoReserva.confirmada)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/garantia/{rid}",
            json={"metodo": "Efectivo"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "Pendiente" in resp.get_json()["mensaje"]

    def test_garantia_con_transferencia(self, client, app):
        """201 — garantía con método Transferencia."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_gar4")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_gar4")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/garantia/{rid}",
            json={"metodo": "Transferencia"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["tipo"] == "Garantia"
        assert data["data"]["metodo"] == "Transferencia"

    def test_garantia_con_tarjeta_mock(self, client, app):
        """201 — garantía con tarjeta usa referencia mock (STRIPE_MOCK=True)."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_gar5")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_gar5")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva(huesped, hab)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(
            f"/api/v1/pagos/garantia/{rid}",
            json={"metodo": "Tarjeta", "payment_method_id": "pm_test_xxx"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["referencia_externa"].startswith("pi_mock_")