"""
Módulo ServicioAdicional — RF-10 (Comedor) y RF-11 (Spa)
Gestiona servicios adicionales vinculados a una reserva en estado Ocupada.
"""
from decimal import Decimal, InvalidOperation

from app import db
from app.models.servicio_adicional import ServicioAdicional, TipoServicio
from app.models.reserva import EstadoReserva, Reserva
from app.models.factura import EstadoFactura, Factura
from app.utils.fecha_helper import ahora_colombia


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
    factura = Factura.query.filter_by(id_reserva=reserva_id).first()
    if not factura:
        return False
    return factura.estado in (EstadoFactura.emitida, EstadoFactura.pagada)


def agregar(reserva_id: int, tipo_str: str, descripcion: str, costo_raw) -> dict:
    """
    Agrega un servicio adicional a una reserva en estado Ocupada.
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
    costo = _validar_costo(costo_raw)

    if not descripcion or not str(descripcion).strip():
        raise ValueError("La descripción del servicio es obligatoria.")
    if len(descripcion.strip()) > 255:
        raise ValueError("La descripción no puede superar 255 caracteres.")

    servicio = ServicioAdicional(
        id_reserva=reserva_id,
        tipo=tipo,
        descripcion=descripcion.strip(),
        costo=costo,
        fecha_hora=ahora_colombia(),
    )
    db.session.add(servicio)
    db.session.commit()
    return servicio.to_dict()


def listar(reserva_id: int) -> dict:
    """
    Lista todos los servicios adicionales de una reserva.
    """
    reserva = _get_reserva(reserva_id)
    servicios = ServicioAdicional.query.filter_by(id_reserva=reserva.id).all()
    items = [s.to_dict() for s in servicios]
    subtotal = sum(
        (Decimal(str(s.costo)) for s in servicios),
        Decimal("0.00")
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
