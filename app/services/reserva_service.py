"""
Reserva Service - Lógica de negocio para reservas
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime
from decimal import Decimal

from flask import current_app

from app import db
from app.models.reserva import EstadoReserva, Reserva
from app.models.habitacion import EstadoHabitacion
from app.models.huesped import Huesped
from app.models.notificacion import Notificacion
from app.models.factura import Factura, EstadoFactura
from app.models.checkin_checkout import CheckInCheckOut
from app.models.pago import EstadoPago, Pago, TipoPago
from app.models.reembolso import EstadoReembolso, Reembolso
from app.utils.fecha_helper import ahora_colombia


def crear(datos, current_user):
    """Crea una nueva reserva."""
    _validar_campos_obligatorios(datos)

    id_habitacion = datos["id_habitacion"]
    fecha_entrada = _parse_fecha(datos["fecha_entrada"])
    fecha_salida = _parse_fecha(datos["fecha_salida"])

    if fecha_entrada < date.today():
        raise ValueError("La fecha de entrada no puede ser en el pasado.")

    if fecha_entrada >= fecha_salida:
        raise ValueError(
            "La fecha de entrada debe ser anterior a la fecha de salida."
        )

    from app.models.habitacion import Habitacion
    habitacion = Habitacion.query.filter_by(
        id=id_habitacion, activo=True
    ).first()
    if not habitacion:
        raise LookupError(f"Habitación con id {id_habitacion} no encontrada.")

    if habitacion.estado != EstadoHabitacion.disponible:
        raise ValueError(
            f"La habitación {habitacion.numero} no está disponible."
        )

    _validar_reserva_no_solapada(id_habitacion, fecha_entrada, fecha_salida)

    id_huesped = _obtener_id_huesped(current_user)

    noches = (fecha_salida - fecha_entrada).days
    precio_noche = Decimal(str(habitacion.precio_noche))
    subtotal = precio_noche * noches
    impuestos = subtotal * Decimal("0.19")
    total = subtotal + impuestos

    reserva = Reserva(
        id_huesped=id_huesped,
        id_habitacion=id_habitacion,
        fecha_entrada=fecha_entrada,
        fecha_salida=fecha_salida,
        noches=noches,
        subtotal=subtotal,
        impuestos=impuestos,
        total=total,
        estado=EstadoReserva.pendiente,
    )

    db.session.add(reserva)
    db.session.flush()

    notificacion = Notificacion(
        id_reserva=reserva.id,
        tipo="confirmacion_reserva",
        mensaje="Tu reserva ha sido creada correctamente.",
        enviado=False,
        fecha_envio=None,
    )
    db.session.add(notificacion)
    db.session.commit()

    return reserva.to_dict()


def obtener_todas(filtros=None):
    """Obtiene todas las reservas con filtros opcionales."""
    query = Reserva.query

    if filtros:
        if filtros.get("estado"):
            try:
                estado = EstadoReserva(filtros["estado"])
                query = query.filter_by(estado=estado)
            except ValueError:
                raise ValueError(
                    f"Estado inválido. Valores permitidos: "
                    f"{[e.value for e in EstadoReserva]}"
                )

        if filtros.get("id_huesped"):
            query = query.filter_by(id_huesped=int(filtros["id_huesped"]))

        if filtros.get("fecha_entrada"):
            fecha = _parse_fecha(filtros["fecha_entrada"])
            query = query.filter_by(fecha_entrada=fecha)

    reservas = query.order_by(Reserva.fecha_entrada.desc()).all()
    return [r.to_dict() for r in reservas]


def obtener_por_id(reserva_id, current_user):
    """Obtiene una reserva por ID."""
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    rol_value = (
        current_user.rol.value
        if hasattr(current_user.rol, 'value')
        else current_user.rol
    )
    if rol_value == "cliente":
        try:
            huesped = Huesped.query.filter_by(
                id_usuario=current_user.id
            ).first()
            if not huesped or reserva.id_huesped != huesped.id:
                raise PermissionError(
                    "No tienes permiso para ver esta reserva."
                )
        except Exception:
            raise PermissionError(
                "No tienes permiso para ver esta reserva."
            )

    return reserva.to_dict()


def obtener_mis_reservas(current_user):
    """Obtiene las reservas del usuario actual (solo para clientes)."""
    try:
        huesped = Huesped.query.filter_by(
            id_usuario=current_user.id
        ).first()
        if not huesped:
            return []

        reservas = Reserva.query.filter_by(
            id_huesped=huesped.id
        ).order_by(Reserva.fecha_entrada.desc()).all()
        return [r.to_dict() for r in reservas]
    except Exception:
        return []


def confirmar(reserva_id):
    """Confirma una reserva y envía email de confirmación."""
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

    try:
        _enviar_email_confirmacion(reserva)
        notificacion = Notificacion.query.filter_by(
            id_reserva=reserva.id, tipo="confirmacion_reserva"
        ).first()
        if notificacion:
            notificacion.enviado = True
            notificacion.fecha_envio = ahora_colombia()
            db.session.commit()
    except Exception:
        pass

    return reserva.to_dict()


def cancelar(reserva_id, motivo=None, current_user=None):
    """Cancela una reserva y genera reembolso automático si hay garantía pagada."""
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    if current_user:
        rol_value = (
            current_user.rol.value
            if hasattr(current_user.rol, 'value')
            else current_user.rol
        )
        if rol_value == "cliente":
            try:
                huesped = Huesped.query.filter_by(
                    id_usuario=current_user.id
                ).first()
                if not huesped or reserva.id_huesped != huesped.id:
                    raise PermissionError(
                        "No tienes permiso para cancelar esta reserva."
                    )
            except Exception:
                raise PermissionError(
                    "No tienes permiso para cancelar esta reserva."
                )

    horas_faltantes = (
        reserva.fecha_entrada - date.today()
    ).total_seconds() / 3600
    if horas_faltantes < 24:
        raise ValueError(
            "No se puede cancelar. Faltan menos de 24 horas para la fecha "
            "de entrada. (RF-04)"
        )

    if reserva.estado == EstadoReserva.cancelada:
        raise ValueError("La reserva ya está cancelada.")

    reserva.estado = EstadoReserva.cancelada
    reserva.motivo_cancelacion = motivo
    reserva.updated_at = ahora_colombia()

    if reserva.habitacion.estado == EstadoHabitacion.ocupada:
        reserva.habitacion.estado = EstadoHabitacion.disponible

    garantia = Pago.query.filter_by(
        id_reserva=reserva_id,
        tipo=TipoPago.garantia,
        estado=EstadoPago.aprobado,
    ).first()
    if garantia and not garantia.reembolso:
        reembolso = Reembolso(
            id_pago=garantia.id,
            monto=garantia.monto,
            motivo=motivo or "Cancelación de reserva",
            estado=EstadoReembolso.solicitado,
        )
        db.session.add(reembolso)
        garantia.estado = EstadoPago.reembolsado

    db.session.commit()
    return reserva.to_dict()


def hacer_checkin(reserva_id, realizado_por_id=None):
    """Realiza el check-in de una reserva."""
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    if reserva.estado != EstadoReserva.confirmada:
        raise ValueError(
            f"No se puede hacer check-in. Estado actual: "
            f"{reserva.estado.value}. "
            f"Solo se puede hacer check-in en reservas confirmadas."
        )

    reserva.estado = EstadoReserva.ocupada
    reserva.habitacion.estado = EstadoHabitacion.ocupada
    reserva.updated_at = ahora_colombia()

    checkin_checkout = CheckInCheckOut(
        id_reserva=reserva.id,
        fecha_checkin=ahora_colombia(),
        realizado_por=realizado_por_id,
    )

    db.session.add(checkin_checkout)
    db.session.commit()

    return reserva.to_dict()


def hacer_checkout(reserva_id, realizado_por_id=None):
    """Realiza el check-out. Requiere liquidación aprobada (SRS RF-13)."""
    reserva = Reserva.query.get(reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")

    if reserva.estado != EstadoReserva.ocupada:
        raise ValueError(
            f"No se puede hacer check-out. Estado actual: "
            f"{reserva.estado.value}. "
            f"Solo se puede hacer check-out en reservas ocupadas."
        )

    liquidacion = Pago.query.filter_by(
        id_reserva=reserva_id,
        tipo=TipoPago.liquidacion,
        estado=EstadoPago.aprobado,
    ).first()
    if not liquidacion:
        raise ValueError(
            "No se puede hacer check-out. Se requiere el pago de liquidación "
            "aprobado antes de emitir la factura. (RF-13)"
        )

    reserva.estado = EstadoReserva.completada
    reserva.habitacion.estado = EstadoHabitacion.disponible
    reserva.updated_at = ahora_colombia()

    checkin_checkout = CheckInCheckOut.query.filter_by(
        id_reserva=reserva.id
    ).first()
    if checkin_checkout:
        checkin_checkout.fecha_checkout = ahora_colombia()

    puntos = reserva.noches * 10
    huesped = Huesped.query.get(reserva.id_huesped)
    if huesped:
        usuario = huesped.usuario
        usuario.puntos_fidelizacion += puntos

    servicios_adicionales_total = Decimal("0")
    if reserva.servicios_adicionales:
        servicios_adicionales_total = sum(
            Decimal(str(s.costo)) for s in reserva.servicios_adicionales
        )

    factura = Factura(
        id_reserva=reserva.id,
        fecha_emision=ahora_colombia(),
        subtotal=reserva.subtotal,
        impuestos=reserva.impuestos,
        servicios_adicionales_total=servicios_adicionales_total,
        total=(
            reserva.subtotal +
            reserva.impuestos +
            servicios_adicionales_total
        ),
        estado=EstadoFactura.pendiente,
    )
    db.session.add(factura)
    db.session.commit()

    resultado = reserva.to_dict()
    resultado["puntos_ganados"] = puntos
    return resultado


def _obtener_id_huesped(current_user):
    """Obtiene el id_huesped del usuario actual."""
    rol_value = (
        current_user.rol.value
        if hasattr(current_user.rol, 'value')
        else current_user.rol
    )
    if rol_value == "cliente":
        huesped = Huesped.query.filter_by(
            id_usuario=current_user.id
        ).first()
        if not huesped:
            raise ValueError(
                "El usuario no tiene un perfil de huésped. "
                "Contacta al administrador."
            )
        return huesped.id

    id_huesped = int(current_user.id)
    huesped = Huesped.query.get(id_huesped)
    if not huesped:
        raise ValueError("Debes proporcionar el id_huesped en los datos.")

    return id_huesped


def _validar_campos_obligatorios(datos):
    """Valida que los campos obligatorios estén presentes."""
    requeridos = ["id_habitacion", "fecha_entrada", "fecha_salida"]
    faltantes = [c for c in requeridos if c not in datos or not datos[c]]
    if faltantes:
        raise ValueError(
            f"Campos obligatorios faltantes: {', '.join(faltantes)}"
        )


def _parse_fecha(fecha_str):
    """Convierte una cadena de fecha a objeto date."""
    if isinstance(fecha_str, date):
        return fecha_str
    if isinstance(fecha_str, datetime):
        return fecha_str.date()
    return datetime.strptime(fecha_str, "%Y-%m-%d").date()


def _validar_reserva_no_solapada(id_habitacion, fecha_entrada, fecha_salida):
    """Valida que no haya reservas solapadas."""
    reservas_conflicto = Reserva.query.filter(
        Reserva.id_habitacion == id_habitacion,
        Reserva.estado != EstadoReserva.cancelada,
        Reserva.fecha_entrada < fecha_salida,
        Reserva.fecha_salida > fecha_entrada
    ).count()

    if reservas_conflicto > 0:
        raise ValueError(
            "La habitación ya tiene una reserva en el rango de fechas "
            "seleccionado."
        )


def _enviar_email_confirmacion(reserva):
    """Envía email de confirmación de reserva por SMTP."""
    try:
        smtp_host = current_app.config.get("SMTP_HOST")
        smtp_port = current_app.config.get("SMTP_PORT", 587)
        smtp_user = current_app.config.get("SMTP_USER")
        smtp_password = current_app.config.get("SMTP_PASSWORD")

        if not all([smtp_host, smtp_user, smtp_password]):
            return

        huesped = Huesped.query.get(reserva.id_huesped)
        if not huesped or not huesped.usuario:
            return

        destinatario = huesped.usuario.email
        nombre_huesped = (
            f"{huesped.usuario.nombre} {huesped.usuario.apellido}"
        )

        asunto = (
            f"Confirmación de Reserva - {reserva.id} - HotelBook Pro"
        )

        cuerpo = f"""
Estimado/a {nombre_huesped},

Nos complace confirmar su reserva en HotelBook Pro.

Detalles de su reserva:
- Reserva ID: {reserva.id}
- Habitación: {reserva.habitacion.numero}
- Tipo: {reserva.habitacion.tipo}
- Fecha de entrada: {reserva.fecha_entrada.strftime('%Y-%m-%d')}
- Fecha de salida: {reserva.fecha_salida.strftime('%Y-%m-%d')}
- Noches: {reserva.noches}
- Subtotal: ${float(reserva.subtotal):.2f}
- Impuestos (19%): ${float(reserva.impuestos):.2f}
- Total: ${float(reserva.total):.2f}

Por favor, realice el check-in 30 minutos antes de su hora de llegada.

Gracias por elegir HotelBook Pro.

Atentamente,
El equipo de HotelBook Pro
"""

        mensaje = MIMEMultipart()
        mensaje["From"] = smtp_user
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto
        mensaje.attach(MIMEText(cuerpo, "plain", "utf-8"))

        servidor = smtplib.SMTP(smtp_host, smtp_port)
        servidor.starttls()
        servidor.login(smtp_user, smtp_password)
        servidor.send_message(mensaje)
        servidor.quit()

    except Exception:
        pass
