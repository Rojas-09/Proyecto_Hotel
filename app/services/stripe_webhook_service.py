"""
Stripe Webhook Service — Procesa eventos asíncronos de Stripe (RF-13 M1)
"""

import stripe
from flask import current_app
from sqlalchemy import select

from app import db
from app.models.pago import EstadoPago, Pago, TipoPago
from app.models.reembolso import EstadoReembolso, Reembolso
from app.models.reserva import EstadoReserva, Reserva
from app.utils.fecha_helper import ahora_colombia


def procesar_evento(payload: bytes, sig_header: str) -> dict:
    """
    Verifica la firma del webhook y delega el evento al manejador
    correspondiente.

    Retorna dict con {"tipo": ..., "procesado": bool, "detalle": ...}
    """
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        return {
            "tipo": "error",
            "procesado": False,
            "detalle": "WEBHOOK_SECRET no configurado",
        }

    try:
        evento = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError:
        return {"tipo": "error", "procesado": False, "detalle": "Payload inválido"}
    except stripe.error.SignatureVerificationError:
        return {
            "tipo": "error",
            "procesado": False,
            "detalle": "Firma del webhook inválida",
        }

    tipo = evento["type"]
    objeto = evento["data"]["object"]

    manejadores = {
        "payment_intent.payment_failed": _manejar_payment_failed,
        "payment_intent.succeeded": _manejar_payment_succeeded,
        "charge.refunded": _manejar_charge_refunded,
    }

    manejador = manejadores.get(tipo)
    if not manejador:
        return {"tipo": tipo, "procesado": False, "detalle": "Evento no manejado"}

    try:
        resultado = manejador(objeto)
        db.session.commit()
        return {"tipo": tipo, "procesado": True, "detalle": resultado}
    except Exception as e:
        db.session.rollback()
        return {"tipo": tipo, "procesado": False, "detalle": str(e)}


def _manejar_payment_failed(objeto: dict) -> str:
    """Registra el pago fallido en BD con el motivo."""
    pi_id = objeto["id"]
    last_error = objeto.get("last_payment_error") or {}
    mensaje = last_error.get("message", "Error desconocido en el pago")

    pago = _buscar_por_payment_intent(pi_id)
    if pago:
        pago.estado = EstadoPago.rechazado
        pago.failure_message = mensaje
        pago.updated_at = ahora_colombia()
        return f"Pago {pago.id} marcado como rechazado: {mensaje}"

    return f"PaymentIntent {pi_id} no asociado a ningún pago local (ignorado)"


def _manejar_payment_succeeded(objeto: dict) -> str:
    """Confirma el pago si llegó como succeeded async."""
    pi_id = objeto["id"]
    pago = _buscar_por_payment_intent(pi_id)
    if not pago:
        return f"PaymentIntent {pi_id} no asociado a ningún pago local (ignorado)"

    if pago.estado != EstadoPago.aprobado:
        pago.estado = EstadoPago.aprobado
        pago.updated_at = ahora_colombia()

        reserva = db.session.get(Reserva, pago.id_reserva)
        if (
            reserva
            and reserva.estado == EstadoReserva.pendiente
            and pago.tipo == TipoPago.garantia
        ):
            reserva.estado = EstadoReserva.confirmada
            reserva.updated_at = ahora_colombia()

        return f"Pago {pago.id} confirmado exitosamente"

    return f"Pago {pago.id} ya estaba aprobado"


def _manejar_charge_refunded(objeto: dict) -> str:
    """Sincroniza el reembolso iniciado desde dashboard Stripe."""
    pi_id = objeto.get("payment_intent")
    if not pi_id:
        return "Evento charge.refunded sin payment_intent (ignorado)"

    pago = _buscar_por_payment_intent(pi_id)
    if not pago:
        return f"PaymentIntent {pi_id} no asociado a ningún pago local (ignorado)"

    monto_reembolsado = objeto.get("amount_refunded", 0)
    if monto_reembolsado and monto_reembolsado > 0:
        pago.estado = EstadoPago.reembolsado
        pago.updated_at = ahora_colombia()

        if not pago.reembolso:
            reembolso = Reembolso(
                id_pago=pago.id,
                monto=pago.monto,
                motivo="Reembolso procesado desde Stripe",
                estado=EstadoReembolso.procesado,
            )
            db.session.add(reembolso)

        return f"Pago {pago.id} marcado como reembolsado"

    return f"Pago {pago.id}: charge.refunded sin monto (ignorado)"


def _buscar_por_payment_intent(pi_id: str):
    """Busca un Pago por stripe_payment_intent_id o referencia_externa."""
    return db.session.execute(
        select(Pago).filter(
            (Pago.stripe_payment_intent_id == pi_id)
            | (Pago.referencia_externa == pi_id)
        )
    ).scalar_one_or_none()
