"""
PuntosFidelidad Controller - Endpoints REST para puntos de fidelización (RF-12)
GET /api/v1/huespedes/<huesped_id>/puntos         → total de puntos
GET /api/v1/huespedes/<huesped_id>/puntos/historial → historial completo
"""

from flask import Blueprint, jsonify

from app.services import puntos_fidelidad_service
from app.utils.jwt_helper import token_required, rol_requerido

puntos_bp = Blueprint("puntos_fidelidad", __name__)


@puntos_bp.route("/<int:huesped_id>/puntos", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista", "gerente")
def obtener_total(current_user, huesped_id):
    """
    GET /api/v1/huespedes/<huesped_id>/puntos

    Retorna el total de puntos de un huésped.
    Roles permitidos: admin, recepcionista, gerente.
    """
    try:
        total = puntos_fidelidad_service.obtener_total(huesped_id)
        return jsonify({
            "success": True,
            "data": {"total": total},
            "mensaje": "Puntos obtenidos correctamente."
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "data": None,
            "mensaje": str(e)
        }), 404


@puntos_bp.route("/<int:huesped_id>/puntos/historial", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista", "gerente")
def listar_historial(current_user, huesped_id):
    """
    GET /api/v1/huespedes/<huesped_id>/puntos/historial

    Retorna el historial de puntos de un huésped.
    Roles permitidos: admin, recepcionista, gerente.
    """
    try:
        historial = puntos_fidelidad_service.listar_historial(huesped_id)
        return jsonify({
            "success": True,
            "data": {"historial": historial, "total": len(historial)},
            "mensaje": "Historial obtenido correctamente."
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "data": None,
            "mensaje": str(e)
        }), 404