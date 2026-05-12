"""
PuntosFidelidad Service - Lógica de negocio para puntos de fidelización (RF-12)
"""

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
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    existente = PuntosFidelidad.query.filter_by(id_reserva=reserva_id).first()
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
    huesped = Huesped.query.get(huesped_id)
    if not huesped:
        raise LookupError(f"Huésped con id {huesped_id} no encontrado.")

    total = db.session.query(db.func.coalesce(
        db.func.sum(PuntosFidelidad.puntos), 0
    )).filter(PuntosFidelidad.id_huesped == huesped_id).scalar()
    return int(total)


def listar_historial(huesped_id):
    """Retorna el historial de puntos de un huésped, ordenados por fecha desc."""
    huesped = Huesped.query.get(huesped_id)
    if not huesped:
        raise LookupError(f"Huésped con id {huesped_id} no encontrado.")

    registros = PuntosFidelidad.query.filter_by(
        id_huesped=huesped_id
    ).order_by(PuntosFidelidad.fecha.desc()).all()
    return [r.to_dict() for r in registros]