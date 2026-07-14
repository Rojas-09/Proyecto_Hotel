import pytest
from decimal import Decimal
from datetime import date, timedelta

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.puntos_fidelidad import PuntosFidelidad
from app.models.reserva import EstadoReserva, Reserva
from app.models.usuario import RolEnum, Usuario
from app.services.puntos_fidelidad_service import (
    listar_canjeos,
    canjear,
    obtener_total,
)


@pytest.fixture
def huesped_con_puntos(app):
    with app.app_context():
        u = Usuario(
            nombre="Test", apellido="Svc",
            email="pf_svc@test.com", rol=RolEnum.cliente,
        )
        u.password = "Pass1234!"
        db.session.add(u)
        db.session.flush()
        h = Huesped(id_usuario=u.id, documento_id="PF-SVC", tipo_documento="CC")
        db.session.add(h)
        db.session.flush()
        hab = Habitacion(
            numero="PF-SVC", tipo=TipoHabitacion.simple,
            precio_noche=Decimal("100000"), capacidad=1,
            estado=EstadoHabitacion.disponible,
        )
        db.session.add(hab)
        db.session.flush()
        r = Reserva(
            id_huesped=h.id, id_habitacion=hab.id,
            fecha_entrada=date.today() + timedelta(days=1),
            fecha_salida=date.today() + timedelta(days=11),
            noches=10, subtotal=Decimal("1000000"),
            impuestos=Decimal("190000"), total=Decimal("1190000"),
            estado=EstadoReserva.completada,
        )
        db.session.add(r)
        db.session.commit()
        db.session.add(PuntosFidelidad(
            id_huesped=h.id, id_reserva=r.id,
            puntos=100, concepto="10 puntos x 10 noches",
        ))
        db.session.commit()
        yield h.id


class TestListarCanjeos:
    def test_retorna_lista(self, app):
        with app.app_context():
            canjeos = listar_canjeos()
            assert len(canjeos) == 5
            assert canjeos[0]["id"] == 1


class TestCanjear:
    def test_huesped_no_existe(self, app):
        with app.app_context():
            with pytest.raises(LookupError, match="no encontrado"):
                canjear(99999, 1)

    def test_opcion_invalida(self, app, huesped_con_puntos):
        with app.app_context():
            with pytest.raises(ValueError, match="Opción de canje inválida"):
                canjear(huesped_con_puntos, 99)

    def test_puntos_insuficientes(self, app, huesped_con_puntos):
        with app.app_context():
            with pytest.raises(ValueError, match="Puntos insuficientes"):
                canjear(huesped_con_puntos, 2)

    def test_exitoso(self, app, huesped_con_puntos):
        with app.app_context():
            resultado = canjear(huesped_con_puntos, 1)
            assert "canje" in resultado
            assert "puntos_restantes" in resultado
            assert resultado["canje"]["puntos"] == -100
            assert resultado["puntos_restantes"] == 0
