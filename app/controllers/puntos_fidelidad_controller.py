"""
PuntosFidelidad Controller - Endpoints REST para puntos de fidelización (RF-12)
GET    /api/v1/huespedes/<huesped_id>/puntos           → total de puntos
GET    /api/v1/huespedes/<huesped_id>/puntos/historial → historial completo
GET    /api/v1/huespedes/<huesped_id>/puntos/canjeos   → opciones de canje
POST   /api/v1/huespedes/<huesped_id>/puntos/canjear   → canjear puntos
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from app import db
from app.models.huesped import Huesped
from app.services import puntos_fidelidad_service
from app.utils.error_helper import handle_service_error
from app.utils.jwt_helper import token_required, rol_requerido

puntos_bp = Blueprint("puntos_fidelidad", __name__)


def _verificar_ownership_puntos(current_user, huesped_id):
    rol_actual = (
        current_user.rol.value
        if hasattr(current_user.rol, 'value')
        else current_user.rol
    )
    if rol_actual == "cliente":
        huesped = db.session.execute(
            select(Huesped).filter_by(id_usuario=current_user.id)
        ).scalar_one_or_none()
        if not huesped or huesped.id != huesped_id:
            raise PermissionError("No tienes permiso para gestionar estos puntos.")


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
        return handle_service_error(e, 404)


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
        return handle_service_error(e, 404)


@puntos_bp.route("/<int:huesped_id>/puntos/canjeos", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista", "gerente", "cliente")
def listar_canjeos(current_user, huesped_id):
    """
    GET /api/v1/huespedes/<huesped_id>/puntos/canjeos

    Retorna las opciones de canje disponibles.
    Roles permitidos: todos los roles autenticados.
    """
    canjeos = puntos_fidelidad_service.listar_canjeos()
    return jsonify({
        "success": True,
        "data": {"canjeos": canjeos},
    }), 200


@puntos_bp.route("/<int:huesped_id>/puntos/canjear", methods=["POST"])
@token_required
@rol_requerido("admin", "recepcionista", "cliente")
def canjear_puntos(current_user, huesped_id):
    """
    POST /api/v1/huespedes/<huesped_id>/puntos/canjear

    Canjea puntos por una opción disponible.
    Body: { "opcion_id": int }

    Roles permitidos: admin, recepcionista, cliente.
    """
    data = request.get_json(silent=True) or {}
    opcion_id = data.get("opcion_id")

    if opcion_id is None:
        return jsonify({
            "success": False,
            "data": None,
            "mensaje": "El campo 'opcion_id' es obligatorio."
        }), 400

    try:
        _verificar_ownership_puntos(current_user, huesped_id)
        resultado = puntos_fidelidad_service.canjear(huesped_id, int(opcion_id))
        return jsonify({
            "success": True,
            "data": resultado,
            "mensaje": "Canje realizado exitosamente."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)
    except PermissionError as e:
        return handle_service_error(e, 403)
