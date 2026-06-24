"""
Pago Service - Lógica de negocio para pagos y reembolsos (RF-13)
"""

from decimal import Decimal
from uuid import uuid4
from sqlalchemy import select

from flask import current_app

from app import db
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app.models.reembolso import EstadoReembolso, Reembolso
from app.models.reserva import EstadoReserva, Reserva
from app.utils.fecha_helper import ahora_colombia

# ---------------------------------------------------------------------------
# Públicas
# ---------------------------------------------------------------------------


def procesar_garantia(
    reserva_id, metodo_str, payment_method_id=None, current_user=None
):
    """
    Procesa el pago de garantía (50 % del total) y confirma la reserva.

    Flujo (SRS RF-13 Fase 1):
      PENDIENTE → [pago 50 %] → CONFIRMADA
    """
    reserva = _obtener_reserva(reserva_id)

    if current_user:
        rol_actual = (
            current_user.rol.value
            if hasattr(current_user.rol, "value")
            else current_user.rol
        )
        if rol_actual == "cliente":
            huesped = db.session.execute(
                select(Huesped).filter_by(id_usuario=current_user.id)
            ).scalar_one_or_none()
            if not huesped or reserva.id_huesped != huesped.id:
                raise PermissionError(
                    "No tienes permiso para procesar el pago de esta reserva."
                )

    _verificar_sin_garantia(reserva_id)

    if reserva.estado != EstadoReserva.pendiente:
        raise ValueError(
            f"La reserva no está en estado Pendiente. "
            f"Estado actual: {reserva.estado.value}"
        )

    metodo = _validar_metodo(metodo_str)
    monto = (
        Decimal(str(reserva.total))
        * Decimal(str(current_app.config["GARANTIA_PORCENTAJE"]))
    ).quantize(Decimal("0.01"))

    stripe_pi_id = None
    failure_msg = None
    if metodo == MetodoPago.tarjeta:
        try:
            stripe_pi_id = _cobrar_stripe(
                monto, payment_method_id, reserva_id, "garantia"
            )
        except ValueError as e:
            failure_msg = str(e)

    es_manual = metodo in (MetodoPago.efectivo, MetodoPago.transferencia)

    estado_pago = (
        EstadoPago.pendiente
        if es_manual
        else (EstadoPago.rechazado if failure_msg else EstadoPago.aprobado)
    )

    pago = Pago(
        id_reserva=reserva_id,
        monto=monto,
        metodo=metodo,
        tipo=TipoPago.garantia,
        estado=estado_pago,
        referencia_externa=stripe_pi_id,
        stripe_payment_intent_id=stripe_pi_id,
        failure_message=failure_msg,
    )
    db.session.add(pago)
    db.session.flush()

    if failure_msg:
        db.session.commit()
        raise ValueError(failure_msg)

    if es_manual:
        db.session.commit()
        return pago.to_dict()

    reserva.estado = EstadoReserva.confirmada
    reserva.updated_at = ahora_colombia()

    db.session.commit()
    return pago.to_dict()


def procesar_liquidacion(reserva_id, metodo_str, payment_method_id=None):
    """
    Procesa el pago de liquidación (saldo restante + servicios adicionales).

    Flujo (SRS RF-13 Fase 2):
      Se llama antes del checkout. Registra el pago; el checkout crea la factura.
    """
    reserva = _obtener_reserva(reserva_id)

    if reserva.estado != EstadoReserva.ocupada:
        raise ValueError(
            f"La reserva no está en estado Ocupada. "
            f"Estado actual: {reserva.estado.value}"
        )

    garantia = _obtener_garantia_aprobada(reserva_id)

    liquidacion_existente = db.session.execute(
        select(Pago).filter_by(
            id_reserva=reserva_id,
            tipo=TipoPago.liquidacion,
            estado=EstadoPago.aprobado,
        )
    ).scalar_one_or_none()
    if liquidacion_existente:
        raise ValueError("Esta reserva ya tiene un pago de liquidación aprobado.")

    servicios_total = _calcular_total_servicios(reserva)
    total_final = Decimal(str(reserva.total)) + servicios_total
    monto = (total_final - Decimal(str(garantia.monto))).quantize(Decimal("0.01"))
    if monto < Decimal("0"):
        monto = Decimal("0")

    metodo = _validar_metodo(metodo_str)
    referencia_externa = None
    if metodo == MetodoPago.tarjeta and monto > Decimal("0"):
        referencia_externa = _cobrar_stripe(
            monto, payment_method_id, reserva_id, "liquidacion"
        )

    pago = Pago(
        id_reserva=reserva_id,
        monto=monto,
        metodo=metodo,
        tipo=TipoPago.liquidacion,
        estado=EstadoPago.aprobado,
        referencia_externa=referencia_externa,
    )
    db.session.add(pago)
    db.session.commit()
    return pago.to_dict()


def obtener_pagos_reserva(reserva_id):
    """Retorna todos los pagos de una reserva."""
    _obtener_reserva(reserva_id)  # lanza LookupError si no existe
    pagos = (
        db.session.execute(select(Pago).filter_by(id_reserva=reserva_id))
        .scalars()
        .all()
    )
    return [p.to_dict() for p in pagos]


def solicitar_reembolso(pago_id, motivo):
    """
    Registra un reembolso para un pago aprobado y, si el método fue tarjeta,
    procesa el reverso en Stripe.
    """
    pago = db.session.get(Pago, pago_id)
    if not pago:
        raise LookupError(f"Pago con id {pago_id} no encontrado.")

    if pago.reembolso:
        raise ValueError("Este pago ya tiene un reembolso registrado.")

    if pago.estado != EstadoPago.aprobado:
        raise ValueError(
            f"Solo se pueden reembolsar pagos aprobados. "
            f"Estado actual: {pago.estado.value}"
        )

    if not motivo or not motivo.strip():
        raise ValueError("El motivo del reembolso es obligatorio.")

    if pago.metodo == MetodoPago.tarjeta and pago.referencia_externa:
        _reversar_stripe(pago.referencia_externa, pago.monto)

    reembolso = Reembolso(
        id_pago=pago_id,
        monto=pago.monto,
        motivo=motivo.strip(),
        estado=EstadoReembolso.procesado,
    )
    db.session.add(reembolso)

    pago.estado = EstadoPago.reembolsado
    db.session.commit()
    return reembolso.to_dict()


def confirmar_pago_manual(pago_id, current_user):
    """
    Confirma un pago manual (efectivo/transferencia) y cambia la reserva a confirmada.

    Flujo:
      Pago PENDIENTE + Reserva PENDIENTE → Pago APROBADO + Reserva CONFIRMADA
    """
    pago = db.session.get(Pago, pago_id)
    if not pago:
        raise LookupError(f"Pago con id {pago_id} no encontrado.")

    if pago.metodo not in (MetodoPago.efectivo, MetodoPago.transferencia):
        raise ValueError(
            "Solo pagos en efectivo o transferencia requieren confirmación manual."
        )

    if pago.estado != EstadoPago.pendiente:
        raise ValueError(
            f"El pago no está pendiente. Estado actual: {pago.estado.value}"
        )

    pago.estado = EstadoPago.aprobado
    pago.confirmado_por = current_user.id
    pago.fecha_confirmacion = ahora_colombia()

    reserva = db.session.get(Reserva, pago.id_reserva)
    if reserva and reserva.estado == EstadoReserva.pendiente:
        reserva.estado = EstadoReserva.confirmada
        reserva.updated_at = ahora_colombia()

    db.session.commit()
    return pago.to_dict()


# ---------------------------------------------------------------------------
# Privadas — validaciones y helpers
# ---------------------------------------------------------------------------


def _obtener_reserva(reserva_id):
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        raise LookupError(f"Reserva con id {reserva_id} no encontrada.")
    return reserva


def _verificar_sin_garantia(reserva_id):
    """
    Verifica que no haya garantía aprobada.
    Si solo existe una garantía RECHAZADA, permite reintento (RF-13 M2).
    """
    garantia = db.session.execute(
        select(Pago).filter_by(
            id_reserva=reserva_id,
            tipo=TipoPago.garantia,
            estado=EstadoPago.aprobado,
        )
    ).scalar_one_or_none()
    if garantia:
        raise ValueError("Esta reserva ya tiene un pago de garantía aprobado.")


def _obtener_garantia_aprobada(reserva_id):
    garantia = db.session.execute(
        select(Pago).filter_by(
            id_reserva=reserva_id,
            tipo=TipoPago.garantia,
            estado=EstadoPago.aprobado,
        )
    ).scalar_one_or_none()
    if not garantia:
        raise ValueError(
            "No existe pago de garantía aprobado para esta reserva. "
            "Procese el pago de garantía antes del checkout."
        )
    return garantia


def _calcular_total_servicios(reserva):
    if not reserva.servicios_adicionales:
        return Decimal("0")
    return sum(Decimal(str(s.costo)) for s in reserva.servicios_adicionales)


def _validar_metodo(metodo_str):
    if not metodo_str:
        raise ValueError(
            f"El campo 'metodo' es obligatorio. "
            f"Valores permitidos: {[m.value for m in MetodoPago]}"
        )
    metodos = {m.value.lower(): m for m in MetodoPago}
    metodo = metodos.get(metodo_str.strip().lower())
    if not metodo:
        raise ValueError(
            f"Método de pago inválido: '{metodo_str}'. "
            f"Valores permitidos: {[m.value for m in MetodoPago]}"
        )
    return metodo


# ---------------------------------------------------------------------------
# Privadas — Stripe
# ---------------------------------------------------------------------------


def _cobrar_stripe(monto, payment_method_id, reserva_id, tipo_pago="pago"):
    """
    Crea y confirma un PaymentIntent en Stripe.
    Usa idempotency key dinámica con uuid para permitir reintentos (RF-13 M2).
    En ambiente testing retorna un ID simulado sin llamar la API.
    """
    if current_app.config.get("STRIPE_MOCK"):
        return f"pi_mock_{reserva_id}_{uuid4().hex[:8]}"

    import stripe

    stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise ValueError(
            "Stripe no está configurado. "
            "Defina STRIPE_SECRET_KEY en las variables de entorno."
        )

    if not payment_method_id:
        raise ValueError("Se requiere 'payment_method_id' para pagos con tarjeta.")

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(monto * 100),
            currency="cop",
            payment_method=payment_method_id,
            confirm=True,
            idempotency_key=(f"reserva-{reserva_id}-{tipo_pago}-{uuid4().hex}"),
            automatic_payment_methods={
                "enabled": True,
                "allow_redirects": "never",
            },
        )
    except stripe.error.CardError as e:
        raise ValueError(f"Tarjeta rechazada: {e.user_message}")
    except stripe.error.StripeError as e:
        raise ValueError(f"Error en pasarela de pagos: {str(e)}")

    if intent.status not in ("succeeded", "requires_capture"):
        raise ValueError(f"Pago no completado. Estado Stripe: {intent.status}")

    return intent.id


def _reversar_stripe(payment_intent_id, monto):
    """
    Procesa el reverso de un pago en Stripe.
    En ambiente testing no llama la API.
    """
    if current_app.config.get("STRIPE_MOCK"):
        return

    import stripe

    stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise ValueError("Stripe no está configurado.")

    try:
        stripe.Refund.create(
            payment_intent=payment_intent_id,
            amount=int(monto * 100),
            idempotency_key=f"refund-{payment_intent_id}-v1",
        )
    except stripe.error.StripeError as e:
        raise ValueError(f"Error procesando reembolso en Stripe: {str(e)}")


def listar(filtros=None):
    """Lista todos los pagos con filtros opcionales."""
    query = Pago.query

    if filtros:
        if filtros.get("estado"):
            try:
                estado = EstadoPago(filtros["estado"])
                query = query.filter_by(estado=estado)
            except ValueError:
                raise ValueError(
                    f"Estado inválido. Valores permitidos: "
                    f"{[e.value for e in EstadoPago]}"
                )

        if filtros.get("tipo"):
            try:
                tipo = TipoPago(filtros["tipo"])
                query = query.filter_by(tipo=tipo)
            except ValueError:
                raise ValueError(
                    f"Tipo inválido. Valores permitidos: "
                    f"{[e.value for e in TipoPago]}"
                )

        if filtros.get("metodo"):
            try:
                metodo = MetodoPago(filtros["metodo"])
                query = query.filter_by(metodo=metodo)
            except ValueError:
                raise ValueError(
                    f"Método inválido. Valores permitidos: "
                    f"{[e.value for e in MetodoPago]}"
                )

        if filtros.get("id_reserva"):
            query = query.filter_by(id_reserva=int(filtros["id_reserva"]))

    pagos = query.order_by(Pago.fecha.desc()).all()
    return [p.to_dict() for p in pagos]


def obtener_por_id(pago_id: int) -> dict:
    """Obtiene un pago por su ID."""
    pago = db.session.get(Pago, pago_id)
    if not pago:
        raise LookupError(f"Pago con ID {pago_id} no encontrado.")
    return pago.to_dict()


def anular(pago_id: int, motivo: str = None) -> dict:
    """Anula un pago (soft-delete para admin)."""
    pago = db.session.get(Pago, pago_id)
    if not pago:
        raise LookupError(f"Pago con ID {pago_id} no encontrado.")

    if pago.estado == EstadoPago.reembolsado:
        raise ValueError("No se puede anular un pago ya reembolsado.")

    if pago.estado == EstadoPago.anulado:
        raise ValueError("El pago ya está anulado.")

    if pago.estado == EstadoPago.rechazado:
        raise ValueError("El pago ya está rechazado.")

    pago.estado = EstadoPago.anulado
    if motivo:
        pago.failure_message = motivo
    db.session.commit()
    return pago.to_dict()
