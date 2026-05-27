"""
PuntosFidelidad Service - Lógica de negocio para puntos de fidelización (RF-12)
"""

from sqlalchemy import select

from app import db
from app.models.puntos_fidelidad import PuntosFidelidad
from app.models.reserva import Reserva
from app.models.huesped import Huesped


def acreditar(reserva_id):
    """
    Acredita puntos de fidelidad tras un checkout exitoso.

    Regla: 10 puntos por noche (noches = fecha_salida - fecha_entrada).
    Solo se acredita una vez por reserva (unique constraint).
    """
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    existente = db.session.execute(
        select(PuntosFidelidad).filter_by(id_reserva=reserva_id)
    ).scalar_one_or_none()
    if existente:
        raise ValueError(
            f"Ya se acreditaron puntos para la reserva {reserva_id}."
        )

    noches = (reserva.fecha_salida - reserva.fecha_entrada).days
    puntos = noches * 10
    concepto = f"10 puntos x {noches} noche{'s' if noches != 1 else ''}"

    registro = PuntosFidelidad(
        id_huesped=reserva.id_huesped,
        id_reserva=reserva_id,
        puntos=puntos,
        concepto=concepto,
    )
    db.session.add(registro)
    db.session.commit()
    return registro.to_dict()


def obtener_total(huesped_id):
    """Retorna la suma de todos los puntos de un huésped."""
    huesped = db.session.get(Huesped, huesped_id)
    if not huesped:
        raise LookupError(f"Huésped con id {huesped_id} no encontrado.")

    total = db.session.query(db.func.coalesce(
        db.func.sum(PuntosFidelidad.puntos), 0
    )).filter(PuntosFidelidad.id_huesped == huesped_id).scalar()
    return int(total)


def listar_historial(huesped_id):
    """Retorna el historial de puntos de un huésped, ordenados por fecha desc."""
    huesped = db.session.get(Huesped, huesped_id)
    if not huesped:
        raise LookupError(f"Huésped con id {huesped_id} no encontrado.")

    registros = db.session.execute(
        select(PuntosFidelidad).filter_by(id_huesped=huesped_id)
        .order_by(PuntosFidelidad.fecha.desc())
    ).scalars().all()
    return [r.to_dict() for r in registros]


CANJES_DISPONIBLES = [
    {"id": 1, "nombre": "10% de descuento en próxima reserva", "puntos_requeridos": 100},
    {"id": 2, "nombre": " upgrade de habitación (Suite)", "puntos_requeridos": 250},
    {"id": 3, "nombre": "1 noche gratis", "puntos_requeridos": 500},
    {"id": 4, "nombre": "Cena romántica en el Comedor", "puntos_requeridos": 150},
    {"id": 5, "nombre": "Sesión de Spa gratuita (60 min)", "puntos_requeridos": 200},
]


def listar_canjeos():
    """Retorna la lista de opciones de canje disponibles."""
    return CANJES_DISPONIBLES


def canjear(huesped_id, opcion_id):
    """
    Canjea puntos por una opción disponible.
    Registra el canje como puntos negativos en el historial.
    """
    huesped = db.session.get(Huesped, huesped_id)
    if not huesped:
        raise LookupError(f"Huésped con id {huesped_id} no encontrado.")

    opcion = next((o for o in CANJES_DISPONIBLES if o["id"] == opcion_id), None)
    if not opcion:
        raise ValueError(
            f"Opción de canje inválida: {opcion_id}. "
            f"Usa GET /huespedes/<id>/puntos/canjeos para ver las opciones."
        )

    total_actual = obtener_total(huesped_id)
    if total_actual < opcion["puntos_requeridos"]:
        raise ValueError(
            f"Puntos insuficientes. Tienes {total_actual} pts, "
            f"necesitas {opcion['puntos_requeridos']} pts para "
            f"'{opcion['nombre']}'."
        )

    registro = PuntosFidelidad(
        id_huesped=huesped_id,
        id_reserva=None,
        puntos=-opcion["puntos_requeridos"],
        concepto=f"Canje: {opcion['nombre']}",
    )
    db.session.add(registro)
    db.session.commit()

    return {
        "canje": registro.to_dict(),
        "puntos_restantes": obtener_total(huesped_id),
    }