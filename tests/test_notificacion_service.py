import pytest
from decimal import Decimal
from datetime import date, timedelta

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.reserva import EstadoReserva, Reserva
from app.models.usuario import RolEnum, Usuario
from app.services.notificacion_service import (
    _validar_tipo,
    listar,
    buscar,
    crear,
    obtener,
    listar_por_reserva,
    actualizar,
    eliminar,
)


@pytest.fixture
def reserva_con_notificacion(app):
    with app.app_context():
        u = Usuario(
            nombre="Huesped",
            apellido="NSvc",
            email="nsvc_test@test.com",
            rol=RolEnum.cliente,
        )
        u.password = "Pass1234!"
        db.session.add(u)
        db.session.flush()
        h = Huesped(id_usuario=u.id, documento_id="NSVC-TEST")
        db.session.add(h)
        hab = Habitacion(
            numero="NSVC",
            tipo=TipoHabitacion.simple,
            precio_noche=Decimal("100000"),
            capacidad=1,
            estado=EstadoHabitacion.disponible,
        )
        db.session.add(hab)
        db.session.flush()
        r = Reserva(
            id_huesped=h.id,
            id_habitacion=hab.id,
            fecha_entrada=date.today() + timedelta(days=1),
            fecha_salida=date.today() + timedelta(days=3),
            noches=2,
            subtotal=Decimal("200000"),
            impuestos=Decimal("38000"),
            total=Decimal("238000"),
            estado=EstadoReserva.confirmada,
        )
        db.session.add(r)
        db.session.commit()
        n = crear(r.id, "ConfirmacionReserva", "Notificación de prueba")
        return r, n


class TestValidarTipo:
    def test_tipo_valido(self, app):
        with app.app_context():
            t = _validar_tipo("ConfirmacionReserva")
            assert t.value == "ConfirmacionReserva"

    def test_tipo_invalido(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Tipo de notificación inválido"):
                _validar_tipo("TipoInexistente")


class TestCrear:
    def test_reserva_inexistente(self, app):
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrada"):
                crear(99999, "ConfirmacionReserva", "Test")


class TestObtener:
    def test_inexistente(self, app):
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrada"):
                obtener(99999)

    def test_inactiva_retorna_lookup_error(self, app, reserva_con_notificacion):
        _, n = reserva_con_notificacion
        with app.app_context():
            eliminar(n["id"])
            with pytest.raises(LookupError, match="no encontrada"):
                obtener(n["id"])


class TestListar:
    def test_filtro_fecha_desde(self, app, reserva_con_notificacion):
        with app.app_context():
            ayer = (date.today() - timedelta(days=1)).isoformat()
            resultado = listar({"fecha_desde": ayer})
            assert len(resultado) >= 1

    def test_filtro_fecha_hasta(self, app, reserva_con_notificacion):
        with app.app_context():
            manana = (date.today() + timedelta(days=1)).isoformat()
            resultado = listar({"fecha_hasta": manana})
            assert len(resultado) >= 1

    def test_filtro_fecha_desde_sin_resultados(self, app):
        with app.app_context():
            futuro = (date.today() + timedelta(days=365)).isoformat()
            resultado = listar({"fecha_desde": futuro})
            assert len(resultado) == 0

    def test_filtro_fecha_invalida(self, app):
        with app.app_context():
            with pytest.raises(ValueError):
                listar({"fecha_desde": "no-es-fecha"})

    def test_filtro_enviado_true(self, app, reserva_con_notificacion):
        _, n = reserva_con_notificacion
        with app.app_context():
            actualizar(n["id"], enviado=True)
            resultado = listar({"enviado": True})
            assert len(resultado) >= 1


class TestBuscar:
    def test_sin_resultados_devuelve_vacio(self, app):
        with app.app_context():
            resultado = buscar("xyzxyzxyz123")
            assert resultado == []


class TestListarPorReserva:
    def test_reserva_inexistente(self, app):
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrada"):
                listar_por_reserva(99999)


class TestEliminar:
    def test_inexistente(self, app):
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrada"):
                eliminar(99999)
