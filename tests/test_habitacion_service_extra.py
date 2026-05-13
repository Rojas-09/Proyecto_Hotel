from datetime import date, timedelta

import pytest

from app import db
from app.models.habitacion import (
    Habitacion,
    EstadoHabitacion,
    TipoHabitacion,
)
from app.services import habitacion_service


def _crear_habitacion(numero, tipo, precio=100, capacidad=1, piso=1):
    h = Habitacion(
        numero=numero,
        tipo=TipoHabitacion(tipo) if isinstance(tipo, str) else tipo,
        descripcion="x",
        precio_noche=precio,
        capacidad=capacidad,
        piso=piso,
        estado=EstadoHabitacion.disponible,
    )
    db.session.add(h)
    db.session.commit()
    return h


def test_obtener_todas_tipo_estado_invalidos(app):
    with app.app_context():
        db.session.query(Habitacion).delete()
        db.session.commit()

    with pytest.raises(ValueError):
        habitacion_service.obtener_todas({"tipo": "invalido"})

    with pytest.raises(ValueError):
        habitacion_service.obtener_todas({"estado": "noexiste"})


def test_crear_duplicate_and_invalid_tipo(app):
    with app.app_context():
        db.session.query(Habitacion).delete()
        db.session.commit()

        datos = {
            "numero": "A1",
            "tipo": TipoHabitacion.simple.value,
            "precio_noche": 120,
            "capacidad": 1,
        }
        r = habitacion_service.crear(datos)
        assert r["numero"] == "A1"

        # duplicate numero
        with pytest.raises(ValueError):
            habitacion_service.crear(datos)

        # invalid tipo
        datos_bad = datos.copy()
        datos_bad["numero"] = "B2"
        datos_bad["tipo"] = "nope"
        with pytest.raises(ValueError):
            habitacion_service.crear(datos_bad)


def test_actualizar_and_eliminar_checks(app):
    with app.app_context():
        db.session.query(Habitacion).delete()
        db.session.commit()

        h1 = _crear_habitacion("100", TipoHabitacion.simple)
        h2 = _crear_habitacion("101", TipoHabitacion.doble)

        # actualizar numero a uno existente -> error
        with pytest.raises(ValueError):
            habitacion_service.actualizar(h1.id, {"numero": "101"})

        # invalid tipo en actualizar
        with pytest.raises(ValueError):
            habitacion_service.actualizar(h1.id, {"tipo": "nope"})

        # precio invalido
        with pytest.raises(ValueError):
            habitacion_service.actualizar(h1.id, {"precio_noche": 0})

        # capacidad invalida
        with pytest.raises(ValueError):
            habitacion_service.actualizar(h1.id, {"capacidad": 0})

        # eliminar inexistente
        with pytest.raises(LookupError):
            habitacion_service.eliminar(999999)

        # eliminar existente
        res = habitacion_service.eliminar(h1.id)
        assert "mensaje" in res


def test_buscar_disponibles_errors_and_success(app):
    with app.app_context():
        db.session.query(Habitacion).delete()
        db.session.commit()

        _crear_habitacion("R1", TipoHabitacion.simple, precio=50)

    # invalid format
    with pytest.raises(ValueError):
        habitacion_service.buscar_disponibles("2027-13-01", "2027-01-02")

    # fecha entrada en pasado
    pasado = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    futura = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    with pytest.raises(ValueError):
        habitacion_service.buscar_disponibles(pasado, futura)

    # fecha entrada >= salida
    f = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    with pytest.raises(ValueError):
        habitacion_service.buscar_disponibles(f, f)

    # tipo invalido
    start = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    end = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
    with pytest.raises(ValueError):
        habitacion_service.buscar_disponibles(start, end, tipo="nope")

    # successful search
    res = habitacion_service.buscar_disponibles(start, end)
    assert isinstance(res, list)
    if res:
        assert "noches" in res[0]
        assert "total_estimado" in res[0]
