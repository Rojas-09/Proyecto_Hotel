from datetime import date, datetime

from app import db
from app.models.reserva import EstadoReserva, Reserva
from app.models.habitacion import EstadoHabitacion
from app.models.usuario import Usuario
from app.utils.fecha_helper import ahora_colombia


def crear(datos, current_user):
    _validar_campos_obligatorios(datos)

    id_habitacion = datos["id_habitacion"]
    fecha_entrada = _parse_fecha(datos["fecha_entrada"])
    fecha_salida = _parse_fecha(datos["fecha_salida"])

    if fecha_entrada < date.today():
        raise ValueError("La fecha de entrada no puede ser en el pasado.")

    if fecha_entrada >= fecha_salida:
        raise ValueError("La fecha de entrada debe ser anterior a la fecha de salida.")

    from app.models.habitacion import Habitacion
    habitacion = Habitacion.query.filter_by(id=id_habitacion, activo=True).first()
    if not habitacion:
        raise LookupError(f"Habitacion con id {id_habitacion} no encontrada.")

    if habitacion.estado != EstadoHabitacion.disponible:
        raise ValueError(f"La habitacion {habitacion.numero} no esta disponible.")

    _validar_reserva_no_solapada(id_habitacion, fecha_entrada, fecha_salida)

    noches = (fecha_salida - fecha_entrada).days
    total = float(habitacion.precio_noche) * noches

    reserva = Reserva(
        id_cliente=current_user.id,
        id_habitacion=id_habitacion,
        fecha_entrada=fecha_entrada,
        fecha_salida=fecha_salida,
        noches=noches,
        total=total,
        estado=EstadoReserva.pendiente,
    )

    db.session.add(reserva)
    db.session.commit()

    return reserva.to_dict()


def obtener_todas(filtros=None):
    query = Reserva.query

    if filtros:
        if filtros.get("estado"):
            try:
                estado = EstadoReserva(filtros["estado"])
                query = query.filter_by(estado=estado)
            except ValueError:
                raise ValueError(
                    f"Estado invalido. Valores permitidos: "
                    f"{[e.value for e in EstadoReserva]}"
                )

        if filtros.get("id_cliente"):
            query = query.filter_by(id_cliente=int(filtros["id_cliente"]))

        if filtros.get("fecha_entrada"):
            fecha = _parse_fecha(filtros["fecha_entrada"])
            query = query.filter_by(fecha_entrada=fecha)

    reservas = query.order_by(Reserva.fecha_entrada.desc()).all()
    return [r.to_dict() for r in reservas]


def obtener_por_id(reserva_id, current_user):
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    if current_user.rol == "cliente" and reserva.id_cliente != current_user.id:
        raise PermissionError("No tienes permiso para ver esta reserva.")

    return reserva.to_dict()


def obtener_mis_reservas(current_user):
    reservas = Reserva.query.filter_by(
        id_cliente=current_user.id
    ).order_by(Reserva.fecha_entrada.desc()).all()
    return [r.to_dict() for r in reservas]


def confirmar(reserva_id):
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    if reserva.estado != EstadoReserva.pendiente:
        raise ValueError(
            f"No se puede confirmar. Estado actual: {reserva.estado.value}. "
            f"Solo se pueden confirmar reservas pendientes."
        )

    reserva.estado = EstadoReserva.confirmada
    reserva.updated_at = ahora_colombia()
    db.session.commit()

    return reserva.to_dict()


def cancelar(reserva_id, motivo=None, current_user=None):
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    if current_user and current_user.rol == "cliente":
        if reserva.id_cliente != current_user.id:
            raise PermissionError("No tienes permiso para cancelar esta reserva.")

    horas_faltantes = (reserva.fecha_entrada - date.today()) * 24
    if horas_faltantes.days < 24:
        raise ValueError(
            "No se puede cancelar. Faltan menos de 24 horas para la fecha de entrada. (RF-04)"
        )

    if reserva.estado == EstadoReserva.cancelada:
        raise ValueError("La reserva ya esta cancelada.")

    reserva.estado = EstadoReserva.cancelada
    reserva.motivo_cancelacion = motivo
    reserva.updated_at = ahora_colombia()

    if reserva.habitacion.estado == EstadoHabitacion.ocupada:
        reserva.habitacion.estado = EstadoHabitacion.disponible

    db.session.commit()

    return reserva.to_dict()


def hacer_checkin(reserva_id):
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    if reserva.estado != EstadoReserva.confirmada:
        raise ValueError(
            f"No se puede hacer check-in. Estado actual: {reserva.estado.value}. "
            f"Solo se puede hacer check-in en reservas confirmadas."
        )

    from app.services import habitacion_service

    habitacion_service.actualizar(
        reserva.id_habitacion,
        {"estado": "Ocupada"}
    )

    reserva.estado = EstadoReserva.ocupada
    reserva.updated_at = ahora_colombia()
    db.session.commit()

    return reserva.to_dict()


def hacer_checkout(reserva_id):
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    if reserva.estado != EstadoReserva.ocupada:
        raise ValueError(
            f"No se puede hacer check-out. Estado actual: {reserva.estado.value}. "
            f"Solo se puede hacer check-out en reservas ocupadas."
        )

    from app.services import habitacion_service

    habitacion_service.actualizar(
        reserva.id_habitacion,
        {"estado": "Disponible"}
    )

    puntos = reserva.noches * 10
    cliente = Usuario.query.get(reserva.id_cliente)
    cliente.puntos_fidelizacion += puntos

    reserva.estado = EstadoReserva.completada
    reserva.updated_at = ahora_colombia()

    db.session.commit()

    resultado = reserva.to_dict()
    resultado["puntos_ganados"] = puntos
    return resultado


def _validar_campos_obligatorios(datos):
    requeridos = ["id_habitacion", "fecha_entrada", "fecha_salida"]
    faltantes = [c for c in requeridos if c not in datos or not datos[c]]
    if faltantes:
        raise ValueError(f"Campos obligatorios faltantes: {', '.join(faltantes)}")


def _parse_fecha(fecha_str):
    if isinstance(fecha_str, date):
        return fecha_str
    return datetime.strptime(fecha_str, "%Y-%m-%d").date()


def _validar_reserva_no_solapada(id_habitacion, fecha_entrada, fecha_salida):
    reservas_conflicto = Reserva.query.filter(
        Reserva.id_habitacion == id_habitacion,
        Reserva.estado != EstadoReserva.cancelada,
        Reserva.fecha_entrada < fecha_salida,
        Reserva.fecha_salida > fecha_entrada
    ).count()

    if reservas_conflicto > 0:
        raise ValueError(
            "La habitacion ya tiene una reserva en el rango de fechas seleccionado."
        )