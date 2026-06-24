"""
Módulo ServicioAdicional — RF-10 (Comedor) y RF-11 (Spa)
Gestiona servicios adicionales vinculados a una reserva en estado Ocupada.
"""

from datetime import timedelta
from decimal import Decimal, InvalidOperation

from app import db
from app.models.servicio_adicional import ServicioAdicional, TipoServicio
from app.models.reserva import EstadoReserva, Reserva
from app.models.factura import EstadoFactura, Factura
from sqlalchemy import select

from app.utils.fecha_helper import ahora_colombia, COLOMBIA_TZ


def _get_reserva(reserva_id: int) -> Reserva:
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        raise LookupError(f"Reserva {reserva_id} no encontrada.")
    return reserva


def _validar_tipo(tipo_str: str):
    if not tipo_str:
        raise ValueError("El tipo de servicio es obligatorio.")
    tipo = next(
        (t for t in TipoServicio if t.value.lower() == tipo_str.strip().lower()),
        None,
    )
    if tipo is None:
        valores = ", ".join(t.value for t in TipoServicio)
        raise ValueError(
            f"Tipo de servicio inválido: '{tipo_str}'. Valores permitidos: {valores}."
        )
    return tipo


def _validar_costo(costo_raw):
    if costo_raw is None:
        raise ValueError("El costo es obligatorio.")
    try:
        costo = Decimal(str(costo_raw)).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ValueError(f"Costo inválido: '{costo_raw}'.")
    if costo <= Decimal("0.00"):
        raise ValueError("El costo debe ser mayor que cero.")
    return costo


def _factura_emitida(reserva_id: int) -> bool:
    factura = db.session.execute(
        select(Factura).filter_by(id_reserva=reserva_id)
    ).scalar_one_or_none()
    if not factura:
        return False
    return factura.estado in (EstadoFactura.emitida, EstadoFactura.pagada)


def _validar_sin_traslapes_spa(
    fecha_hora,
    duracion_minutos: int,
    recurso: str = None,
    servicio_id_excluir: int = None,
):
    """
    Valida que un servicio de tipo Spa no se traslape con otro del mismo
    recurso (sala/masajista) a nivel global (RF-11).

    Si el servicio no especifica recurso, se omite la validación
    (backward compatibility).
    """
    if not recurso:
        return

    desde = fecha_hora
    hasta = fecha_hora + timedelta(minutes=duracion_minutos)

    filtros = [
        ServicioAdicional.tipo == TipoServicio.spa,
        ServicioAdicional.recurso == recurso,
        ServicioAdicional.fecha_hora < hasta,
    ]

    if servicio_id_excluir:
        filtros.append(ServicioAdicional.id != servicio_id_excluir)

    existentes = (
        db.session.execute(select(ServicioAdicional).filter(*filtros)).scalars().all()
    )

    for s in existentes:
        s_desde = s.fecha_hora
        if s_desde.tzinfo is None:
            s_desde = s_desde.replace(tzinfo=COLOMBIA_TZ)
        s_hasta = s_desde + timedelta(minutes=s.duracion_minutos or 60)
        if s_desde < hasta and s_hasta > desde:
            raise ValueError(
                "La fecha y hora seleccionada se traslapa con otro servicio "
                f"de Spa en el recurso '{recurso}' "
                f"(ID {s.id}: "
                f"{s_desde.strftime('%H:%M')} - "
                f"{s_hasta.strftime('%H:%M')})."
            )


def agregar(
    reserva_id: int,
    tipo_str: str,
    descripcion: str,
    costo_raw,
    duracion_minutos: int = None,
    recurso: str = None,
    fecha_hora=None,
) -> dict:
    """
    Agrega un servicio adicional a una reserva en estado Ocupada.
    Si el tipo es Spa, valida que no haya traslapes de horario
    por recurso (sala/masajista) a nivel global (RF-11).
    """
    reserva = _get_reserva(reserva_id)

    if reserva.estado != EstadoReserva.ocupada:
        raise ValueError(
            f"Solo se pueden agregar servicios a reservas en estado Ocupada "
            f"(estado actual: {reserva.estado.value})."
        )

    if _factura_emitida(reserva_id):
        raise ValueError(
            "No se pueden agregar servicios: la reserva ya tiene una factura emitida."
        )

    tipo = _validar_tipo(tipo_str)
    if duracion_minutos is None:
        duracion_minutos = 60
    elif duracion_minutos < 15 or duracion_minutos > 480:
        raise ValueError("La duración debe estar entre 15 y 480 minutos.")
    costo = _validar_costo(costo_raw)

    if not descripcion or not str(descripcion).strip():
        raise ValueError("La descripción del servicio es obligatoria.")
    if len(descripcion.strip()) > 255:
        raise ValueError("La descripción no puede superar 255 caracteres.")

    momento = fecha_hora or ahora_colombia()

    if tipo == TipoServicio.spa:
        _validar_sin_traslapes_spa(momento, duracion_minutos, recurso)

    servicio = ServicioAdicional(
        id_reserva=reserva_id,
        tipo=tipo,
        recurso=recurso.strip() if recurso else None,
        descripcion=descripcion.strip(),
        costo=costo,
        fecha_hora=momento,
        duracion_minutos=duracion_minutos,
    )
    db.session.add(servicio)
    db.session.commit()
    return servicio.to_dict()


def listar(reserva_id: int) -> dict:
    """
    Lista todos los servicios adicionales de una reserva.
    """
    reserva = _get_reserva(reserva_id)
    servicios = (
        db.session.execute(select(ServicioAdicional).filter_by(id_reserva=reserva.id))
        .scalars()
        .all()
    )
    items = [s.to_dict() for s in servicios]
    subtotal = sum(
        (Decimal(str(s.costo)) for s in servicios), Decimal("0.00")
    ).quantize(Decimal("0.01"))
    return {"servicios": items, "subtotal": float(subtotal), "total": len(items)}


def obtener(servicio_id: int) -> dict:
    """Obtiene un servicio por su id."""
    servicio = db.session.get(ServicioAdicional, servicio_id)
    if not servicio:
        raise LookupError(f"Servicio {servicio_id} no encontrado.")
    return servicio.to_dict()


def eliminar(servicio_id: int) -> dict:
    """
    Elimina un servicio adicional.
    """
    servicio = db.session.get(ServicioAdicional, servicio_id)
    if not servicio:
        raise LookupError(f"Servicio {servicio_id} no encontrado.")

    reserva = _get_reserva(servicio.id_reserva)

    if reserva.estado not in (EstadoReserva.ocupada, EstadoReserva.confirmada):
        raise ValueError(
            "Solo se pueden eliminar servicios de reservas en estado Ocupada o Confirmada."
        )

    if _factura_emitida(servicio.id_reserva):
        raise ValueError(
            "No se puede eliminar el servicio: la reserva ya tiene una factura emitida."
        )

    info = servicio.to_dict()
    db.session.delete(servicio)
    db.session.commit()
    return info


def actualizar(servicio_id: int, descripcion: str = None, costo_raw=None) -> dict:
    """
    Actualiza descripción o costo de un servicio existente.
    """
    servicio = db.session.get(ServicioAdicional, servicio_id)
    if not servicio:
        raise LookupError(f"Servicio {servicio_id} no encontrado.")

    if _factura_emitida(servicio.id_reserva):
        raise ValueError(
            "No se puede modificar el servicio: la reserva ya tiene una factura emitida."
        )

    if descripcion is not None:
        if not str(descripcion).strip():
            raise ValueError("La descripción no puede estar vacía.")
        if len(descripcion.strip()) > 255:
            raise ValueError("La descripción no puede superar 255 caracteres.")
        servicio.descripcion = descripcion.strip()

    if costo_raw is not None:
        servicio.costo = _validar_costo(costo_raw)

    db.session.commit()
    return servicio.to_dict()
