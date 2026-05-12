"""
Controlador ServicioAdicional — RF-10 (Comedor) y RF-11 (Spa)
"""
from flask import Blueprint, jsonify, request

from app.services import servicio_adicional_service
from app.utils.jwt_helper import rol_requerido, token_required

servicio_adicional_bp = Blueprint("servicio_adicional", __name__)


@servicio_adicional_bp.route(
    "/api/v1/reservas/<int:reserva_id>/servicios", methods=["POST"]
)
@token_required
@rol_requerido("recepcionista", "admin")
def agregar_servicio(current_user, reserva_id: int):
    """
    POST /api/v1/reservas/<reserva_id>/servicios

    Body: { tipo, descripcion, costo }
    Retorna 201 { servicio: ... }
    """
    data = request.get_json(silent=True) or {}
    try:
        servicio = servicio_adicional_service.agregar(
            reserva_id=reserva_id,
            tipo_str=data.get("tipo"),
            descripcion=data.get("descripcion"),
            costo_raw=data.get("costo"),
        )
        return jsonify({"servicio": servicio}), 201
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403


@servicio_adicional_bp.route(
    "/api/v1/reservas/<int:reserva_id>/servicios", methods=["GET"]
)
@token_required
@rol_requerido("recepcionista", "admin", "gerente")
def listar_servicios(current_user, reserva_id: int):
    """Retorna 200 { servicios: [...], subtotal: N, total: N }"""
    try:
        resultado = servicio_adicional_service.listar(reserva_id)
        return jsonify(resultado), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404


@servicio_adicional_bp.route(
    "/api/v1/servicios/<int:servicio_id>", methods=["GET"]
)
@token_required
@rol_requerido("recepcionista", "admin")
def obtener_servicio(current_user, servicio_id: int):
    """Retorna 200 { servicio: ... }"""
    try:
        servicio = servicio_adicional_service.obtener(servicio_id)
        return jsonify({"servicio": servicio}), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404


@servicio_adicional_bp.route(
    "/api/v1/servicios/<int:servicio_id>", methods=["PUT"]
)
@token_required
@rol_requerido("recepcionista", "admin")
def actualizar_servicio(current_user, servicio_id: int):
    """
    PUT /api/v1/servicios/<servicio_id>

    Body: { descripcion?, costo? }
    Retorna 200 { servicio: ... }
    """
    data = request.get_json(silent=True) or {}
    try:
        servicio = servicio_adicional_service.actualizar(
            servicio_id=servicio_id,
            descripcion=data.get("descripcion"),
            costo_raw=data.get("costo"),
        )
        return jsonify({"servicio": servicio}), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@servicio_adicional_bp.route(
    "/api/v1/servicios/<int:servicio_id>", methods=["DELETE"]
)
@token_required
@rol_requerido("admin")
def eliminar_servicio(current_user, servicio_id: int):
    """Retorna 200 { mensaje: ..., servicio: ... }"""
    try:
        servicio = servicio_adicional_service.eliminar(servicio_id)
        return jsonify({"mensaje": "Servicio eliminado.", "servicio": servicio}), 200
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
