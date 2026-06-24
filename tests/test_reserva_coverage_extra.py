"""Tests de cobertura para reserva_service.py — caminos de error no cubiertos."""

import pytest
from datetime import date, timedelta

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.usuario import RolEnum, Usuario
from app.models.reserva import EstadoReserva, Reserva
import app.services.reserva_service as svc


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


def _habitacion(numero="101", tipo=TipoHabitacion.doble):
    h = Habitacion(
        numero=numero,
        tipo=tipo,
        precio_noche=200000,
        capacidad=2,
        piso=1,
        estado=EstadoHabitacion.disponible,
    )
    db.session.add(h)
    db.session.flush()
    return h


def _reserva_completada(huesped, habitacion):
    from app.utils.fecha_helper import ahora_colombia

    r = Reserva(
        id_huesped=huesped.id,
        id_habitacion=habitacion.id,
        fecha_entrada=date.today() - timedelta(days=5),
        fecha_salida=date.today() - timedelta(days=3),
        noches=2,
        subtotal=400000,
        impuestos=76000,
        total=476000,
        estado=EstadoReserva.completada,
        created_at=ahora_colombia(),
        updated_at=ahora_colombia(),
    )
    db.session.add(r)
    db.session.flush()
    return r


class TestObtenerTodasErrores:
    """obtener_todas — filtro estado inválido."""

    def test_estado_invalido(self, app):
        """101-102: ValueError con estado inválido."""
        with app.app_context():
            with pytest.raises(ValueError, match="Estado inválido"):
                svc.obtener_todas({"estado": "inexistente"})


class TestObtenerPorIdPermisos:
    """obtener_por_id — cliente ve reserva ajena."""

    def test_cliente_reserva_ajena(self, app):
        """134: PermissionError cuando cliente ve reserva de otro."""
        with app.app_context():
            u1 = _usuario(RolEnum.cliente, "dueño")
            h1 = _huesped(u1)
            u2 = _usuario(RolEnum.cliente, "otro")
            hab = _habitacion()
            r = _reserva_completada(h1, hab)
            db.session.commit()
            with pytest.raises(PermissionError, match="No tienes permiso"):
                svc.obtener_por_id(r.id, u2)


class TestObtenerMisReservasBorde:
    """obtener_mis_reservas — usuario sin huésped."""

    def test_sin_huesped(self, app):
        """147: retorna [] si el usuario no tiene perfil de huésped."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "sinhuesp")
            db.session.commit()
            resultado = svc.obtener_mis_reservas(u)
            assert resultado == []


class TestConfirmarErrores:
    """confirmar — caminos de error."""

    def test_reserva_no_encontrada(self, app):
        """160: LookupError cuando reserva no existe."""
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrada"):
                svc.confirmar(99999)


class TestHacerCheckinErrores:
    """hacer_checkin — caminos de error."""

    def test_reserva_no_encontrada(self, app):
        """251: LookupError."""
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrada"):
                svc.hacer_checkin(99999)

    def test_estado_incorrecto(self, app):
        """254: ValueError si no está confirmada."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "chkerr")
            h = _huesped(u)
            hab = _habitacion()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() + timedelta(days=5),
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=400000,
                impuestos=76000,
                total=476000,
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()
            with pytest.raises(ValueError, match="check-in"):
                svc.hacer_checkin(r.id)


class TestHacerCheckoutErrores:
    """hacer_checkout — caminos de error."""

    def test_reserva_no_encontrada(self, app):
        """280: LookupError."""
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrada"):
                svc.hacer_checkout(99999)

    def test_sin_liquidacion(self, app):
        """297: ValueError cuando no hay liquidación aprobada."""
        with app.app_context():
            u = _usuario(RolEnum.admin, "chkoutadm")
            h = _huesped(u)
            hab = _habitacion()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() - timedelta(days=3),
                fecha_salida=date.today() - timedelta(days=1),
                noches=2,
                subtotal=400000,
                impuestos=76000,
                total=476000,
                estado=EstadoReserva.ocupada,
            )
            db.session.add(r)
            db.session.commit()
            with pytest.raises(ValueError, match="liquidación"):
                svc.hacer_checkout(r.id)


class TestCancelarErrores:
    """cancelar — caminos de error."""

    def test_reserva_no_encontrada(self, app):
        """190: LookupError cuando reserva no existe."""
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrada"):
                svc.cancelar(99999)

    def test_menos_24h(self, app):
        """211: ValueError cuando faltan < 24h."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "c24h")
            h = _huesped(u)
            hab = _habitacion()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() + timedelta(hours=12),
                fecha_salida=date.today() + timedelta(days=2),
                noches=2,
                subtotal=400000,
                impuestos=76000,
                total=476000,
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()
            with pytest.raises(ValueError, match="menos de 24 horas"):
                svc.cancelar(r.id, motivo="urgente", current_user=u)

    def test_ya_cancelada(self, app):
        """217: ValueError cuando ya está cancelada."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "ycanc")
            h = _huesped(u)
            hab = _habitacion()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() + timedelta(days=10),
                fecha_salida=date.today() + timedelta(days=12),
                noches=2,
                subtotal=400000,
                impuestos=76000,
                total=476000,
                estado=EstadoReserva.cancelada,
            )
            db.session.add(r)
            db.session.commit()
            with pytest.raises(ValueError, match="ya está cancelada"):
                svc.cancelar(r.id, current_user=u)


class TestHelpers:
    """Funciones helper."""

    def test_obtener_id_huesped_no_cliente_sin_datos(self, app):
        """362-364: ValueError cuando no-cliente no provee id_huesped."""
        with app.app_context():
            u = _usuario(RolEnum.admin, "noclient")
            db.session.commit()
            with pytest.raises(ValueError, match="id_huesped"):
                svc._obtener_id_huesped(u)

    def test_validar_campos_faltantes(self, app):
        """374: ValueError con campos obligatorios faltantes."""
        with app.app_context():
            with pytest.raises(ValueError, match="obligatorios"):
                svc._validar_campos_obligatorios({"nombre": "test"})

    def test_parse_fecha_date_obj(self, app):
        """382: acepta objeto date."""
        d = date.today()
        assert svc._parse_fecha(d) == d

    def test_reserva_solapada(self, app):
        """400: ValueError con rango de fechas solapado."""
        with app.app_context():
            hab = _habitacion()
            r = Reserva(
                id_huesped=1,
                id_habitacion=hab.id,
                fecha_entrada=date.today() + timedelta(days=5),
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=400000,
                impuestos=76000,
                total=476000,
                estado=EstadoReserva.confirmada,
            )
            db.session.add(r)
            db.session.commit()
            with pytest.raises(ValueError, match="ya tiene una reserva"):
                svc._validar_reserva_no_solapada(
                    hab.id,
                    date.today() + timedelta(days=6),
                    date.today() + timedelta(days=8),
                )


class TestEnviarEmailSMTPError:
    """_enviar_email_confirmacion — SMTP falla silenciosamente."""

    def test_smtp_falla(self, app):
        """466-467: except Exception: pass."""
        from unittest.mock import patch as mock_patch

        with app.app_context():
            u = _usuario(RolEnum.cliente, "mailerr")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva_completada(h, hab)
            db.session.commit()
            with mock_patch("smtplib.SMTP", side_effect=Exception("SMTP down")):
                svc._enviar_email_confirmacion(r)
