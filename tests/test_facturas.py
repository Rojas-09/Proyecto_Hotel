"""
Tests del módulo Facturación (RF-06).
Cubre endpoints: consulta, emisión, descarga y anulación de facturas.
"""

import os
import tempfile
from decimal import Decimal

import pytest

from app import db
from app.models.factura import EstadoFactura, Factura
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app.models.reserva import EstadoReserva, Reserva
from app.models.servicio_adicional import ServicioAdicional, TipoServicio
from app.models.usuario import RolEnum, Usuario
from app.utils.jwt_helper import generar_token


def _crear_usuario(rol: RolEnum, sufijo: str) -> Usuario:
    u = Usuario(
        nombre="Test",
        apellido=sufijo,
        email=f"test_{sufijo}_{id(sufijo)}@hotel.com",
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
        numero=f"10{random.randint(1, 999):03d}",
        tipo=TipoHabitacion.doble,
        precio_noche=Decimal("150000.00"),
        capacidad=2,
        piso=1,
        estado=EstadoHabitacion.disponible,
    )
    db.session.add(hab)
    db.session.flush()
    return hab


def _crear_reserva_completada(huesped, habitacion) -> Reserva:
    from datetime import date, timedelta
    hoy = date.today()
    entrada = hoy - timedelta(days=5)
    salida = hoy - timedelta(days=2)
    reserva = Reserva(
        id_huesped=huesped.id,
        id_habitacion=habitacion.id,
        fecha_entrada=entrada,
        fecha_salida=salida,
        noches=3,
        subtotal=Decimal("450000.00"),
        impuestos=Decimal("85500.00"),
        total=Decimal("535500.00"),
        estado=EstadoReserva.completada,
    )
    db.session.add(reserva)
    db.session.flush()
    return reserva


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
    db.session.flush()
    return f


def _crear_servicio(reserva, tipo: TipoServicio, costo: Decimal) -> ServicioAdicional:
    s = ServicioAdicional(
        id_reserva=reserva.id,
        tipo=tipo,
        descripcion="Servicio adicional de prueba",
        costo=costo,
    )
    db.session.add(s)
    return s


def _crear_pago_liquidacion(reserva: Reserva) -> Pago:
    monto = Decimal(str(reserva.total)) - (Decimal(str(reserva.total)) * Decimal("0.50"))
    p = Pago(
        id_reserva=reserva.id,
        monto=monto.quantize(Decimal("0.01")),
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
# TestObtenerFactura
# ---------------------------------------------------------------------------

class TestObtenerFactura:
    """GET /api/v1/facturas/reserva/<reserva_id>"""

    def test_get_factura_existe(self, client, app):
        """200 — obtiene factura por reserva_id."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_fac1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_fac1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.pendiente)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.get(f"/api/v1/facturas/reserva/{rid}", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id_reserva"] == rid

    def test_get_factura_no_encontrada(self, client, app):
        """404 — no existe factura para esa reserva."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_fac2")
            db.session.commit()
            token = _token(admin)

        resp = client.get("/api/v1/facturas/reserva/99999", headers=_auth(token))
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False

    def test_get_factura_sin_token(self, client, app):
        """401 — endpoint requiere autenticación."""
        resp = client.get("/api/v1/facturas/reserva/1")
        assert resp.status_code == 401

    def test_get_factura_cliente_sin_permiso(self, client, app):
        """403 — cliente no tiene rol admin/recepcionista."""
        with app.app_context():
            cliente_u = _crear_usuario(RolEnum.cliente, "cli_fac2")
            huesped = _crear_huesped(cliente_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.pendiente)
            db.session.commit()
            token = _token(cliente_u)
            rid = reserva.id

        resp = client.get(f"/api/v1/facturas/reserva/{rid}", headers=_auth(token))
        assert resp.status_code == 403

    def test_get_factura_recepcionista_ok(self, client, app):
        """200 — recepcionista puede consultar facturas."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_fac1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_fac3")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.pendiente)
            db.session.commit()
            token = _token(recep)
            rid = reserva.id

        resp = client.get(f"/api/v1/facturas/reserva/{rid}", headers=_auth(token))
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# TestEmitirFactura
# ---------------------------------------------------------------------------

class TestEmitirFactura:
    """POST /api/v1/facturas/reserva/<reserva_id>/emitir"""

    def test_emitir_factura_pendiente(self, client, app):
        """201 — emite factura pendiente correctamente."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_emit1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_emit1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.pendiente)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(f"/api/v1/facturas/reserva/{rid}/emitir", headers=_auth(token))
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["estado"] == "Emitida"
        assert data["data"]["pdf_path"] is not None

    def test_emitir_pdf_creado_en_disco(self, client, app):
        """Verifica que el archivo PDF se crea físicamente."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_emit2")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_emit2")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.pendiente)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(f"/api/v1/facturas/reserva/{rid}/emitir", headers=_auth(token))
        assert resp.status_code == 201
        pdf_path = resp.get_json()["data"]["pdf_path"]
        assert pdf_path is not None
        assert os.path.exists(pdf_path), f"PDF no encontrado en: {pdf_path}"

    def test_emitir_factura_ya_emitida(self, client, app):
        """400 — no se puede reemitir factura ya emitida."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_emit3")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_emit3")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.emitida)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(f"/api/v1/facturas/reserva/{rid}/emitir", headers=_auth(token))
        assert resp.status_code == 400
        assert "ya fue" in resp.get_json()["mensaje"].lower()

    def test_emitir_factura_pagada(self, client, app):
        """400 — no se puede emitir factura pagada."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_emit4")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_emit4")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.pagada)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(f"/api/v1/facturas/reserva/{rid}/emitir", headers=_auth(token))
        assert resp.status_code == 400

    def test_emitir_como_cliente_denegado(self, client, app):
        """403 — cliente no puede emitir facturas."""
        with app.app_context():
            cliente_u = _crear_usuario(RolEnum.cliente, "cli_emit5")
            huesped = _crear_huesped(cliente_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.pendiente)
            db.session.commit()
            token = _token(cliente_u)
            rid = reserva.id

        resp = client.post(f"/api/v1/facturas/reserva/{rid}/emitir", headers=_auth(token))
        assert resp.status_code == 403

    def test_emitir_factura_no_existe(self, client, app):
        """404 — reserva sin factura."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_emit6")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_emit6")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(f"/api/v1/facturas/reserva/{rid}/emitir", headers=_auth(token))
        assert resp.status_code == 404

    def test_emitir_con_servicios_adicionales(self, client, app):
        """201 — emite factura incluyendo servicios adicionales en el PDF."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_emit7")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_emit7")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.pendiente)
            _crear_servicio(reserva, TipoServicio.comedor, Decimal("50000.00"))
            _crear_servicio(reserva, TipoServicio.spa, Decimal("80000.00"))
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.post(f"/api/v1/facturas/reserva/{rid}/emitir", headers=_auth(token))
        assert resp.status_code == 201
        data = resp.get_json()
        assert float(data["data"]["servicios_adicionales_total"]) > 0


# ---------------------------------------------------------------------------
# TestDescargarFactura
# ---------------------------------------------------------------------------

class TestDescargarFactura:
    """GET /api/v1/facturas/reserva/<reserva_id>/descargar"""

    def test_descargar_factura_emitida(self, client, app):
        """200 — descarga PDF de factura emitida."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_desc1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_desc1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            factura = _crear_factura(reserva, EstadoFactura.emitida)
            db.session.commit()
            rid = reserva.id
            token = _token(admin)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 fake")
            temp_path = f.name

        with app.app_context():
            f_record = Factura.query.filter_by(id_reserva=rid).first()
            f_record.pdf_path = temp_path
            db.session.commit()

        resp = client.get(f"/api/v1/facturas/reserva/{rid}/descargar", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"

        os.unlink(temp_path)

    def test_descargar_factura_sin_pdf(self, client, app):
        """404 — factura emitida sin archivo PDF."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_desc2")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_desc2")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.emitida)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.get(f"/api/v1/facturas/reserva/{rid}/descargar", headers=_auth(token))
        assert resp.status_code == 400

    def test_descargar_cliente_su_reserva(self, client, app):
        """200 — cliente descarga su propia factura."""
        with app.app_context():
            cliente_u = _crear_usuario(RolEnum.cliente, "cli_desc3")
            huesped = _crear_huesped(cliente_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.emitida)
            db.session.commit()
            token = _token(cliente_u)
            rid = reserva.id

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 fake")
            temp_path = f.name

        with app.app_context():
            f_record = Factura.query.filter_by(id_reserva=rid).first()
            f_record.pdf_path = temp_path
            db.session.commit()

        resp = client.get(f"/api/v1/facturas/reserva/{rid}/descargar", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"

        os.unlink(temp_path)

    def test_descargar_cliente_otra_reserva(self, client, app):
        """403 — cliente no puede descargar factura de otro huésped."""
        rid = None
        huesped_id_dueño = None
        email_dueño = None
        with app.app_context():
            cliente_u = _crear_usuario(RolEnum.cliente, "cli_desc4")
            huesped = _crear_huesped(cliente_u)
            huesped_id_dueño = huesped.id
            email_dueño = cliente_u.email
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            _crear_factura(reserva, EstadoFactura.emitida)
            db.session.commit()
            rid = reserva.id

        email_otro = None
        with app.app_context():
            otro_u = _crear_usuario(RolEnum.cliente, "cli_desc5")
            db.session.add(otro_u)
            db.session.flush()
            Huesped(
                id_usuario=otro_u.id,
                documento_id=f"CC{hash('99999') % 100000}",
                tipo_documento="CC",
            )
            db.session.commit()
            email_otro = otro_u.email

        with app.app_context():
            otro_u2 = Usuario.query.filter_by(email=email_otro).first()
            otro_token = _token(otro_u2)

        resp = client.get(f"/api/v1/facturas/reserva/{rid}/descargar", headers=_auth(otro_token))
        assert resp.status_code == 403

    def test_descargar_factura_no_existe(self, client, app):
        """404 — reserva sin factura."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_desc3")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_desc6")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            db.session.commit()
            token = _token(admin)
            rid = reserva.id

        resp = client.get(f"/api/v1/facturas/reserva/{rid}/descargar", headers=_auth(token))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestAnularFactura
# ---------------------------------------------------------------------------

class TestAnularFactura:
    """PUT /api/v1/facturas/<factura_id>/anular"""

    def test_anular_factura_emitida(self, client, app):
        """200 — admin anula factura emitida."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_anu1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_anu1")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            factura = _crear_factura(reserva, EstadoFactura.emitida)
            db.session.commit()
            fid = factura.id
            token = _token(admin)

        resp = client.put(
            f"/api/v1/facturas/{fid}/anular",
            json={"motivo": "Error en datos del cliente"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["estado"] == "Anulada"
        assert "motivo_anulacion" in data["data"]

    def test_anular_factura_pagada_denegado(self, client, app):
        """400 — no se puede anular factura pagada."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_anu2")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_anu2")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            factura = _crear_factura(reserva, EstadoFactura.pagada)
            db.session.commit()
            fid = factura.id
            token = _token(admin)

        resp = client.put(
            f"/api/v1/facturas/{fid}/anular",
            json={"motivo": "Intento de anulación"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert "pagada" in resp.get_json()["mensaje"].lower()

    def test_anular_sin_rol_admin(self, client, app):
        """403 — recepcionista no puede anular facturas."""
        with app.app_context():
            recep = _crear_usuario(RolEnum.recepcionista, "rec_anu1")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_anu3")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            factura = _crear_factura(reserva, EstadoFactura.emitida)
            db.session.commit()
            fid = factura.id
            token = _token(recep)

        resp = client.put(
            f"/api/v1/facturas/{fid}/anular",
            json={"motivo": "Recep intenta"},
            headers=_auth(token),
        )
        assert resp.status_code == 403

    def test_anular_factura_ya_anulada(self, client, app):
        """400 — no se puede anular dos veces."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_anu3")
            huesped_u = _crear_usuario(RolEnum.cliente, "cli_anu4")
            huesped = _crear_huesped(huesped_u)
            hab = _crear_habitacion()
            reserva = _crear_reserva_completada(huesped, hab)
            factura = _crear_factura(reserva, EstadoFactura.anulada)
            db.session.commit()
            fid = factura.id
            token = _token(admin)

        resp = client.put(
            f"/api/v1/facturas/{fid}/anular",
            json={"motivo": "Segunda anulación"},
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_anular_factura_no_existe(self, client, app):
        """404 — factura con ID inexistente."""
        with app.app_context():
            admin = _crear_usuario(RolEnum.admin, "adm_anu4")
            db.session.commit()
            token = _token(admin)

        resp = client.put(
            "/api/v1/facturas/99999/anular",
            json={"motivo": "Factura inexistente"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_anular_factura_sin_token(self, client, app):
        """401 — requiere autenticación."""
        resp = client.put("/api/v1/facturas/1/anular", json={"motivo": "Test"})
        assert resp.status_code == 401