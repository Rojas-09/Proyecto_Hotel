"""
Huesped Controller - Endpoints de gestión de huéspedes
GET  /api/v1/huespedes              → Listar todos [admin, recepcionista]
GET  /api/v1/huespedes/<id>         → Obtener por ID [admin, recepcionista]
GET  /api/v1/huespedes/buscar?q=... → Buscar [admin, recepcionista]
PUT  /api/v1/huespedes/<id>         → Actualizar [admin, recepcionista]
"""

from flask import Blueprint, jsonify, request

import app.services.huesped_service as huesped_service
from app.utils.jwt_helper import token_required, rol_requerido

huesped_bp = Blueprint("huespedes", __name__, url_prefix="/api/v1/huespedes")


@huesped_bp.route("/", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def obtener_todos(current_user):
    """Obtiene todos los huéspedes."""
    try:
        huespedes = huesped_service.obtener_todos()
        return jsonify({
            "success": True,
            "data": huespedes,
            "total": len(huespedes),
            "message": "Huéspedes obtenidos correctamente."
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Error interno del servidor.",
            "detail": str(e)
        }), 500


@huesped_bp.route("/<int:huesped_id>", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def obtener_por_id(current_user, huesped_id):
    """Obtiene un huésped por ID."""
    try:
        huesped = huesped_service.obtener_por_id(huesped_id)
        return jsonify({
            "success": True,
            "data": huesped,
            "message": "Huésped obtenido correctamente."
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Error interno del servidor.",
            "detail": str(e)
        }), 500


@huesped_bp.route("/buscar", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def buscar(current_user):
    """Busca huéspedes por nombre, apellido, email o documento_id."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({
            "success": False,
            "message": "Parámetro 'q' requerido."
        }), 400

    try:
        resultados = huesped_service.buscar(q)
        return jsonify({
            "success": True,
            "data": resultados,
            "total": len(resultados),
            "message": "Búsqueda realizada correctamente."
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Error interno del servidor.",
            "detail": str(e)
        }), 500


@huesped_bp.route("/<int:huesped_id>", methods=["PUT"])
@token_required
@rol_requerido("admin", "recepcionista")
def actualizar(current_user, huesped_id):
    """Actualiza un huésped."""
    datos = request.get_json(silent=True)
    if not datos:
        return jsonify({
            "success": False,
            "message": "Body JSON requerido."
        }), 400

    try:
        huesped = huesped_service.actualizar(huesped_id, datos)
        return jsonify({
            "success": True,
            "data": huesped,
            "message": "Huésped actualizado correctamente."
        }), 200
    except LookupError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Error interno del servidor.",
            "detail": str(e)
        }), 500
