"""
Tests del módulo Reportes (RF-08).
Cubre endpoints: ocupación, ingresos, estadísticas.
"""

import os
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import db
from app.models.factura import EstadoFactura, Factura
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app.models.reserva import EstadoReserva, Reserva
from app.models.usuario import RolEnum, Usuario
from app.utils.jwt_helper import generar_token


def _crear_usuario(rol: RolEnum, sufijo: str) -> Usuario:
    u = Usuario(
        nombre="Test",
        apellido=sufijo,
        email=f"reporte_{sufijo}_{id(sufijo)}@hotel.com",
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


def _crear_habitacion(tipo: TipoHabitacion = TipoHabitacion.doble) -> Habitacion:
    import random
    hab = Habitacion(
        numero=f"20{random.randint(1, 999):03d}",
        tipo=tipo,
        precio_noche=Decimal("150000.00"),
        capacidad=2,
        piso=1,
        estado=EstadoHabitacion.disponible,
    )
    db.session.add(hab)
    db.session.flush()
    return hab


def _crear_reserva(huesped, habitacion, estado: EstadoReserva, dias_offset=5) -> Reserva:
    hoy = date.today()
    entrada = hoy + timedelta(days=dias_offset)
    salida = entrada + timedelta(days=2)
    reserva = Reserva(
        id_huesped=huesped.id,
        id_habitacion=habitacion.id,
        fecha_entrada=entrada,
        fecha_salida=salida,
        noches=2,
        subtotal=Decimal("300000.00"),
        impuestos=Decimal("57000.00"),
        total=Decimal("357000.00"),
        estado=estado,
    )
    db.session.add(reserva)
    db.session.flush()
    return reserva


def _crear_pago_aprobado(reserva: Reserva, monto: Decimal = None) -> Pago:
    m = monto or Decimal(str(reserva.total))
    p = Pago(
        id_reserva=reserva.id,
        monto=m.quantize(Decimal("0.01")),
        metodo=MetodoPago.efectivo,
        tipo=TipoPago.liquidacion,
        estado=EstadoPago.aprobado,
    )
    db.session.add(p)
    return p


def _crear_factura(reserva: Reserva, estado: EstadoFactura = EstadoFactura.pendiente) -> Factura:
    f = Factura(
        id_reserva=reserva.id,
        subtotal=reserva.subtotal,
        impuestos=reserva.impuestos,
        servicios_adicionales_total=Decimal("0.00"),
        total=reserva.total,
        estado=estado,
    )
    db.session.add(f)
    return f


def _token(usuario: Usuario) -> str:
    rol = usuario.rol.value if hasattr(usuario.rol, "value") else usuario.rol
    return generar_token(usuario.id, usuario.email, rol)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _fechas():
    hoy = date.today()
    return (
        (hoy - timedelta(days=30)).strftime("%Y-%m-%d"),
        hoy.strftime("%Y-%m-%d"),
    )


# ---------------------------------------------------------------------------
# TestReporteOcupacion
# ---------------------------------------------------------------------------

class TestReporteOcupacion:
    """GET /api/v1/reportes/ocupacion"""

    def test_ocupacion_xlsx_ok(self, client, app):
        """200 — genera reporte de ocupación en xlsx."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_ocup1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_ocup1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion(TipoHabitacion.doble)
            reserva = _crear_reserva(huesped, hab, EstadoReserva.completada)
            db.session.commit()
            token = _token(gerente)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/ocupacion?fecha_inicio={fini}&fecha_fin={ffin}&formato=xlsx",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        ct = resp.content_type
        assert "spreadsheet" in ct or "excel" in ct or "openxmlformats" in ct

    def test_ocupacion_pdf_ok(self, client, app):
        """200 — genera reporte de ocupación en pdf."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_ocup2")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_ocup2")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion(TipoHabitacion.suite)
            reserva = _crear_reserva(huesped, hab, EstadoReserva.completada)
            db.session.commit()
            token = _token(gerente)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/ocupacion?fecha_inicio={fini}&fecha_fin={ffin}&formato=pdf",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert "pdf" in resp.content_type.lower()

    def test_ocupacion_sin_token(self, client, app):
        """401 — requiere autenticación."""
        fini, ffin = _fechas()
        resp = client.get(
            f"/api/v1/reportes/ocupacion?fecha_inicio={fini}&fecha_fin={ffin}"
        )
        assert resp.status_code == 401

    def test_ocupacion_cliente_denegado(self, client, app):
        """403 — cliente no tiene rol gerente/admin."""
        with app.app_context():
            cliente_u = _crear_usuario(RolEnum.cliente, "cli_ocup3")
            huesped = _crear_huesped(cliente_u)
            hab = _crear_habitacion(TipoHabitacion.simple)
            reserva = _crear_reserva(huesped, hab, EstadoReserva.completada)
            db.session.commit()
            token = _token(cliente_u)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/ocupacion?fecha_inicio={fini}&fecha_fin={ffin}",
            headers=_auth(token),
        )
        assert resp.status_code == 403

    def test_ocupacion_fechas_invalidas(self, client, app):
        """400 — fechas en formato incorrecto."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_ocup4")
            db.session.commit()
            token = _token(gerente)

        resp = client.get(
            "/api/v1/reportes/ocupacion?fecha_inicio=2025-13-01&fecha_fin=invalid",
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_ocupacion_fechas_invertidas(self, client, app):
        """400 — fecha inicio posterior a fecha fin."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_ocup5")
            db.session.commit()
            token = _token(gerente)

        resp = client.get(
            "/api/v1/reportes/ocupacion?fecha_inicio=2025-12-31&fecha_fin=2025-01-01",
            headers=_auth(token),
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# TestReporteIngresos
# ---------------------------------------------------------------------------

class TestReporteIngresos:
    """GET /api/v1/reportes/ingresos"""

    def test_ingresos_xlsx_ok(self, client, app):
        """200 — genera reporte de ingresos en xlsx."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_ing1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_ing1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion(TipoHabitacion.deluxe)
            reserva = _crear_reserva(huesped, hab, EstadoReserva.completada)
            _crear_pago_aprobado(reserva)
            db.session.commit()
            token = _token(gerente)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/ingresos?fecha_inicio={fini}&fecha_fin={ffin}&formato=xlsx",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        ct = resp.content_type
        assert "spreadsheet" in ct or "excel" in ct or "openxmlformats" in ct

    def test_ingresos_pdf_ok(self, client, app):
        """200 — genera reporte de ingresos en pdf."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_ing2")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_ing2")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion(TipoHabitacion.suite)
            reserva = _crear_reserva(huesped, hab, EstadoReserva.completada)
            _crear_pago_aprobado(reserva)
            db.session.commit()
            token = _token(gerente)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/ingresos?fecha_inicio={fini}&fecha_fin={ffin}&formato=pdf",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert "pdf" in resp.content_type.lower()

    def test_ingresos_recepcionista_denegado(self, client, app):
        """403 — recepcionista no tiene acceso a reportes."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_ing1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_ing3")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion(TipoHabitacion.doble)
            reserva = _crear_reserva(huesped, hab, EstadoReserva.completada)
            _crear_pago_aprobado(reserva)
            db.session.commit()
            token = _token(recep)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/ingresos?fecha_inicio={fini}&fecha_fin={ffin}",
            headers=_auth(token),
        )
        assert resp.status_code == 403

    def test_ingresos_sin_token(self, client, app):
        """401 — requiere autenticación."""
        fini, ffin = _fechas()
        resp = client.get(f"/api/v1/reportes/ingresos?fecha_inicio={fini}&fecha_fin={ffin}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# TestReporteEstadisticas
# ---------------------------------------------------------------------------

class TestReporteEstadisticas:
    """GET /api/v1/reportes/estadisticas"""

    def test_estadisticas_xlsx_ok(self, client, app):
        """200 — genera reporte de estadísticas en xlsx."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_est1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_est1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion(TipoHabitacion.suite)
            reserva = _crear_reserva(huesped, hab, EstadoReserva.confirmada)
            db.session.commit()
            token = _token(gerente)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/estadisticas?fecha_inicio={fini}&fecha_fin={ffin}&formato=xlsx",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        ct = resp.content_type
        assert "spreadsheet" in ct or "excel" in ct or "openxmlformats" in ct

    def test_estadisticas_pdf_ok(self, client, app):
        """200 — genera reporte de estadísticas en pdf."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_est2")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_est2")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion(TipoHabitacion.doble)
            reserva = _crear_reserva(huesped, hab, EstadoReserva.ocupada)
            db.session.commit()
            token = _token(gerente)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/estadisticas?fecha_inicio={fini}&fecha_fin={ffin}&formato=pdf",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert "pdf" in resp.content_type.lower()

    def test_estadisticas_sin_fecha_inicio(self, client, app):
        """400 — falta fecha_inicio."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_est3")
            db.session.commit()
            token = _token(gerente)

        resp = client.get(
            "/api/v1/reportes/estadisticas?fecha_fin=2025-12-31",
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_estadisticas_sin_fecha_fin(self, client, app):
        """400 — falta fecha_fin."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_est4")
            db.session.commit()
            token = _token(gerente)

        resp = client.get(
            "/api/v1/reportes/estadisticas?fecha_inicio=2025-01-01",
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_estadisticas_admin_ok(self, client, app):
        """200 — admin puede generar estadísticas."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_est1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_est3")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion(TipoHabitacion.simple)
            reserva = _crear_reserva(huesped, hab, EstadoReserva.completada)
            db.session.commit()
            token = _token(admin)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/estadisticas?fecha_inicio={fini}&fecha_fin={ffin}",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        ct = resp.content_type
        assert "spreadsheet" in ct or "excel" in ct or "openxmlformats" in ct

    def test_estadisticas_sin_token(self, client, app):
        """401 — requiere autenticación."""
        fini, ffin = _fechas()
        resp = client.get(
            f"/api/v1/reportes/estadisticas?fecha_inicio={fini}&fecha_fin={ffin}"
        )
        assert resp.status_code == 401

    def test_estadisticas_formato_invalido(self, client, app):
        """400 — formato no soportado."""
        with app.app_context():
            gerente = _crear_usuario(RolEnum.gerente, "ger_est5")
            db.session.commit()
            token = _token(gerente)
            fini, ffin = _fechas()

        resp = client.get(
            f"/api/v1/reportes/estadisticas?fecha_inicio={fini}&fecha_fin={ffin}&formato=csv",
            headers=_auth(token),
        )
        assert resp.status_code == 400