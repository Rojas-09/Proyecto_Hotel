"""
Notificacion Service - Lógica de negocio para notificaciones
"""

from sqlalchemy import select

from app import db
from app.models.notificacion import Notificacion, TipoNotificacion
from app.models.reserva import Reserva
from app.utils.fecha_helper import ahora_colombia


def _validar_tipo(tipo_str):
    try:
        return TipoNotificacion(tipo_str)
    except ValueError:
        raise ValueError(
            f"Tipo de notificación inválido: '{tipo_str}'. "
            f"Valores válidos: {[t.value for t in TipoNotificacion]}"
        )


def crear(id_reserva, tipo, mensaje):
    reserva = db.session.get(Reserva, id_reserva)
    if not reserva:
        raise LookupError(f"Reserva con id {id_reserva} no encontrada.")

    tipo_enum = _validar_tipo(tipo)

    notificacion = Notificacion(
        id_reserva=id_reserva,
        tipo=tipo_enum,
        mensaje=mensaje,
    )
    db.session.add(notificacion)
    db.session.commit()
    return notificacion.to_dict()


def obtener(id):
    notificacion = db.session.get(Notificacion, id)
    if not notificacion or not notificacion.activo:
        raise LookupError(f"Notificación con id {id} no encontrada.")
    return notificacion.to_dict()


def listar(filtros=None):
    query = select(Notificacion).filter_by(activo=True).order_by(Notificacion.created_at.desc())

    if filtros:
        if filtros.get("tipo"):
            try:
                tipo = TipoNotificacion(filtros["tipo"])
                query = query.filter(Notificacion.tipo == tipo)
            except ValueError:
                raise ValueError(
                    f"Tipo inválido. Valores permitidos: "
                    f"{[t.value for t in TipoNotificacion]}"
                )

        if filtros.get("enviado") is not None:
            query = query.filter(Notificacion.enviado == bool(filtros["enviado"]))

        if filtros.get("fecha_desde"):
            from datetime import date
            fecha = date.fromisoformat(filtros["fecha_desde"])
            query = query.filter(Notificacion.created_at >= fecha)

        if filtros.get("fecha_hasta"):
            from datetime import date
            fecha = date.fromisoformat(filtros["fecha_hasta"])
            query = query.filter(Notificacion.created_at <= fecha)

    notificaciones = db.session.execute(query).scalars().all()
    return [n.to_dict() for n in notificaciones]


def buscar(query_str: str):
    """Busca notificaciones por mensaje (contiene)."""
    if not query_str or not query_str.strip():
        raise ValueError("Debe proporcionar un término de búsqueda.")

    q = query_str.strip().lower()
    notificaciones = db.session.execute(
        select(Notificacion)
        .filter(Notificacion.activo)
        .filter(db.func.lower(Notificacion.mensaje).like(f"%{q}%"))
        .order_by(Notificacion.created_at.desc())
    ).scalars().all()
    return [n.to_dict() for n in notificaciones]


def listar_por_reserva(reserva_id):
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    notificaciones = db.session.execute(
        select(Notificacion)
        .filter_by(id_reserva=reserva_id, activo=True)
        .order_by(Notificacion.created_at.desc())
    ).scalars().all()
    return [n.to_dict() for n in notificaciones]


def actualizar(id, **kwargs):
    notificacion = db.session.get(Notificacion, id)
    if not notificacion:
        raise LookupError(f"Notificación con id {id} no encontrada.")

    if "mensaje" in kwargs:
        notificacion.mensaje = kwargs["mensaje"]
    if "tipo" in kwargs:
        notificacion.tipo = _validar_tipo(kwargs["tipo"])
    if "enviado" in kwargs:
        notificacion.enviado = bool(kwargs["enviado"])
        if notificacion.enviado and not notificacion.fecha_envio:
            notificacion.fecha_envio = ahora_colombia()

    db.session.commit()
    return notificacion.to_dict()


def marcar_enviado(id, fecha_envio=None):
    notificacion = db.session.get(Notificacion, id)
    if not notificacion or not notificacion.activo:
        raise LookupError(f"Notificación con id {id} no encontrada.")

    notificacion.enviado = True
    notificacion.fecha_envio = fecha_envio or ahora_colombia()
    db.session.commit()
    return notificacion.to_dict()


def eliminar(id):
    notificacion = db.session.get(Notificacion, id)
    if not notificacion or not notificacion.activo:
        raise LookupError(f"Notificación con id {id} no encontrada.")

    notificacion.activo = False
    db.session.commit()
