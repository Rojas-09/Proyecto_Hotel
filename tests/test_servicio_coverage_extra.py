"""Test de cobertura para servicio_adicional_service.py — caminos de error no cubiertos."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.usuario import RolEnum, Usuario
from app.models.reserva import EstadoReserva, Reserva
from app.models.servicio_adicional import ServicioAdicional, TipoServicio
from app.models.factura import Factura, EstadoFactura
import app.services.servicio_adicional_service as svc


def _usuario(rol, tag):
    u = Usuario(nombre="U", apellido=tag, email=f"{tag}_{id(tag)}@h.com", rol=rol)
    u.password = "pass"
    db.session.add(u)
    db.session.flush()
    return u


def _huesped(usuario):
    h = Huesped(id_usuario=usuario.id, documento_id=f"CC{usuario.id:05d}")
    db.session.add(h)
    db.session.flush()
    return h


def _habitacion():
    h = Habitacion(
        numero="999",
        tipo=TipoHabitacion.simple,
        precio_noche=150000,
        capacidad=2,
        piso=1,
        estado=EstadoHabitacion.disponible,
    )
    db.session.add(h)
    db.session.flush()
    return h


class TestValidarCosto:
    """_validar_costo — caminos borde."""

    def test_invalid_operation(self, app):
        """43-44: InvalidOperation."""
        with app.app_context():
            with pytest.raises(ValueError, match="Costo inválido"):
                svc._validar_costo("no_un_numero")


class TestAgregarErrores:
    """agregar — descripción muy larga."""

    def test_descripcion_muy_larga(self, app):
        """82: ValueError descripción > 255."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "descL")
            h = _huesped(u)
            hab = _habitacion()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() - timedelta(days=2),
                fecha_salida=date.today(),
                noches=2,
                subtotal=300000,
                impuestos=57000,
                total=357000,
                estado=EstadoReserva.ocupada,
            )
            db.session.add(r)
            db.session.commit()
            with pytest.raises(ValueError, match="255"):
                svc.agregar(r.id, "comedor", "x" * 300, 50000)


class TestObtenerErrores:
    """obtener — servicio no encontrado."""

    def test_no_encontrado(self, app):
        """114-117: LookupError."""
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrado"):
                svc.obtener(99999)


class TestEliminarErrores:
    """eliminar — estados no permitidos."""

    def test_reserva_estado_invalido(self, app):
        """131: ValueError si la reserva no está ocupada/confirmada."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "delErr")
            h = _huesped(u)
            hab = _habitacion()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() - timedelta(days=5),
                fecha_salida=date.today() - timedelta(days=3),
                noches=2,
                subtotal=300000,
                impuestos=57000,
                total=357000,
                estado=EstadoReserva.completada,
            )
            db.session.add(r)
            db.session.flush()
            s = ServicioAdicional(
                id_reserva=r.id,
                tipo=TipoServicio.comedor,
                descripcion="Test",
                costo=Decimal("50000"),
            )
            db.session.add(s)
            db.session.commit()
            with pytest.raises(ValueError, match="eliminar servicios"):
                svc.eliminar(s.id)


class TestActualizarErrores:
    """actualizar — caminos de error."""

    def test_descripcion_vacia(self, app):
        """161: ValueError descripción vacía."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "updEmp")
            h = _huesped(u)
            hab = _habitacion()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() - timedelta(days=2),
                fecha_salida=date.today(),
                noches=2,
                subtotal=300000,
                impuestos=57000,
                total=357000,
                estado=EstadoReserva.ocupada,
            )
            db.session.add(r)
            db.session.flush()
            s = ServicioAdicional(
                id_reserva=r.id,
                tipo=TipoServicio.spa,
                descripcion="Un servicio",
                costo=Decimal("80000"),
            )
            db.session.add(s)
            db.session.commit()
            with pytest.raises(ValueError, match="vacía"):
                svc.actualizar(s.id, descripcion="   ")

    def test_descripcion_muy_larga(self, app):
        """163: ValueError descripción > 255."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "updLng")
            h = _huesped(u)
            hab = _habitacion()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() - timedelta(days=2),
                fecha_salida=date.today(),
                noches=2,
                subtotal=300000,
                impuestos=57000,
                total=357000,
                estado=EstadoReserva.ocupada,
            )
            db.session.add(r)
            db.session.flush()
            s = ServicioAdicional(
                id_reserva=r.id,
                tipo=TipoServicio.comedor,
                descripcion="Original",
                costo=Decimal("30000"),
            )
            db.session.add(s)
            db.session.commit()
            with pytest.raises(ValueError, match="255"):
                svc.actualizar(s.id, descripcion="x" * 300)

    def test_factura_emitida(self, app):
        """155: ValueError si ya hay factura emitida."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "updFac")
            h = _huesped(u)
            hab = _habitacion()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() - timedelta(days=2),
                fecha_salida=date.today(),
                noches=2,
                subtotal=300000,
                impuestos=57000,
                total=357000,
                estado=EstadoReserva.ocupada,
            )
            db.session.add(r)
            db.session.flush()
            s = ServicioAdicional(
                id_reserva=r.id,
                tipo=TipoServicio.comedor,
                descripcion="Comida",
                costo=Decimal("40000"),
            )
            db.session.add(s)
            f = Factura(
                id_reserva=r.id,
                subtotal=300000,
                impuestos=57000,
                servicios_adicionales_total=40000,
                total=397000,
                estado=EstadoFactura.emitida,
            )
            db.session.add(f)
            db.session.commit()
            with pytest.raises(ValueError, match="factura emitida"):
                svc.actualizar(s.id, descripcion="Nueva descripción")
