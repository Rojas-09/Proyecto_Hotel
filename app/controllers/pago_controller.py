"""
Pago Controller - Endpoints REST para pagos y reembolsos (RF-13)
"""
from flask import Blueprint, jsonify, request

from app.schemas.pago_schema import PagoGarantiaSchema, PagoLiquidacionSchema
from app.services import pago_service
from app.services import stripe_webhook_service
from app.utils.error_helper import handle_service_error
from app.utils.jwt_helper import rol_requerido, token_required

pago_bp = Blueprint("pago", __name__, url_prefix="/api/v1/pagos")


@pago_bp.route("/garantia/<int:reserva_id>", methods=["POST"])
@token_required
@rol_requerido("cliente", "recepcionista", "admin")
def procesar_garantia(current_user, reserva_id):
    """
    POST /api/v1/pagos/garantia/<reserva_id>

    Procesa el pago de garantía (50 %) y confirma la reserva.
    Roles permitidos: cliente, recepcionista, admin.
    """
    datos = request.get_json() or {}
    errors = PagoGarantiaSchema().validate(datos)
    if errors:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": errors}
        }), 422

    metodo = datos.get("metodo")
    payment_method_id = datos.get("payment_method_id")

    try:
        resultado = pago_service.procesar_garantia(
            reserva_id, metodo, payment_method_id, current_user
        )
        return jsonify({
            "success": True, "data": resultado,
            "mensaje": "Garantía procesada correctamente."
        }), 201
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)
    except PermissionError as e:
        return handle_service_error(e, 403)


@pago_bp.route("/<int:pago_id>/confirmar", methods=["PUT"])
@token_required
@rol_requerido("recepcionista", "admin")
def confirmar_pago_manual(current_user, pago_id):
    """
    PUT /api/v1/pagos/<pago_id>/confirmar

    Confirma un pago manual (efectivo/transferencia) y activa la reserva.
    Roles permitidos: recepcionista, admin.
    """
    try:
        resultado = pago_service.confirmar_pago_manual(pago_id, current_user)
        return jsonify({
            "success": True, "data": resultado,
            "mensaje": "Pago confirmado correctamente."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)


@pago_bp.route("/liquidacion/<int:reserva_id>", methods=["POST"])
@token_required
@rol_requerido("recepcionista", "admin")
def procesar_liquidacion(current_user, reserva_id):
    """
    POST /api/v1/pagos/liquidacion/<reserva_id>

    Procesa el pago de liquidación (saldo restante + servicios adicionales).
    Roles permitidos: recepcionista, admin.
    """
    datos = request.get_json() or {}
    errors = PagoLiquidacionSchema().validate(datos)
    if errors:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": errors}
        }), 422

    metodo = datos.get("metodo")
    payment_method_id = datos.get("payment_method_id")

    try:
        resultado = pago_service.procesar_liquidacion(
            reserva_id, metodo, payment_method_id
        )
        return jsonify({
            "success": True, "data": resultado,
            "mensaje": "Liquidación procesada correctamente."
        }), 201
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)


@pago_bp.route("/reserva/<int:reserva_id>", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def obtener_pagos_reserva(current_user, reserva_id):
    """
    GET /api/v1/pagos/reserva/<reserva_id>

    Retorna todos los pagos de una reserva.
    Roles permitidos: admin, recepcionista.
    """
    try:
        pagos = pago_service.obtener_pagos_reserva(reserva_id)
        return jsonify({
            "success": True, "data": pagos, "total": len(pagos),
            "mensaje": "Pagos obtenidos correctamente."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)


@pago_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    """
    POST /api/v1/pagos/webhook

    Recibe eventos asíncronos de Stripe (RF-13 M1).
    NO requiere autenticación — la verificación es por firma.
    """
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    resultado = stripe_webhook_service.procesar_evento(payload, sig_header)

    if not resultado["procesado"]:
        return jsonify(resultado), 400

    return jsonify(resultado), 200


@pago_bp.route("/reembolso/<int:pago_id>", methods=["POST"])
@token_required
@rol_requerido("admin")
def solicitar_reembolso(current_user, pago_id):
    """
    POST /api/v1/pagos/reembolso/<pago_id>

    Registra y procesa un reembolso para un pago aprobado.
    Roles permitidos: admin.
    """
    datos = request.get_json() or {}
    motivo = datos.get("motivo")

    try:
        resultado = pago_service.solicitar_reembolso(pago_id, motivo)
        return jsonify({
            "success": True, "data": resultado,
            "mensaje": "Reembolso solicitado correctamente."
        }), 201
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)


@pago_bp.route("", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def listar_pagos(current_user):
    """
    GET /api/v1/pagos

    Lista todos los pagos con filtros opcionales:
    - estado: pendiente, aprobado, rechazado, reembolsado
    - tipo: garantia, liquidacion
    - metodo: tarjeta, efectivo, transferencia
    - id_reserva
    Roles permitidos: admin, recepcionista.
    """
    filtros = {
        "estado": request.args.get("estado"),
        "tipo": request.args.get("tipo"),
        "metodo": request.args.get("metodo"),
        "id_reserva": request.args.get("id_reserva"),
    }
    filtros = {k: v for k, v in filtros.items() if v is not None}

    try:
        pagos = pago_service.listar(filtros or None)
        return jsonify({
            "success": True,
            "data": pagos,
            "total": len(pagos),
            "mensaje": "Pagos obtenidos correctamente."
        }), 200
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)


@pago_bp.route("/<int:pago_id>", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def obtener_pago(current_user, pago_id):
    """
    GET /api/v1/pagos/<pago_id>

    Obtiene un pago por ID.
    Roles permitidos: admin, recepcionista.
    """
    try:
        pago = pago_service.obtener_por_id(pago_id)
        return jsonify({
            "success": True,
            "data": pago,
            "mensaje": "Pago encontrado."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)


@pago_bp.route("/<int:pago_id>", methods=["DELETE"])
@token_required
@rol_requerido("admin")
def eliminar_pago(current_user, pago_id):
    """
    DELETE /api/v1/pagos/<pago_id>

    Anula (soft-delete) un pago.
    Roles permitidos: admin.
    """
    datos = request.get_json(silent=True) or {}
    motivo = datos.get("motivo", "Anulado por administrador")

    try:
        pago_service.anular(pago_id, motivo)
        return jsonify({
            "success": True,
            "data": None,
            "mensaje": "Pago anulado correctamente."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)
