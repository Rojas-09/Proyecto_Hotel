"""
Auth Controller - Endpoints de autenticación
POST /api/v1/auth/register      → Registro de cliente
POST /api/v1/auth/register-admin → Crear primer admin (solo si no hay admins)
POST /api/v1/auth/login          → Login + JWT
GET  /api/v1/auth/me             → Datos del usuario autenticado
POST /api/v1/auth/usuarios       → Crear cualquier rol (solo Admin)
"""

from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.utils.jwt_helper import token_required, rol_requerido

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register-admin", methods=["POST"])
def register_admin():
    """Crea el primer administrador. Solo funciona si no hay admins en la DB."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Body JSON requerido."}
        }), 400
    result, status = AuthService.crear_primer_admin(data)
    return jsonify(result), status


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Body JSON requerido."}
        }), 400
    result, status = AuthService.registrar(data)
    return jsonify(result), status


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Body JSON requerido."}
        }), 400
    result, status = AuthService.login(data)
    return jsonify(result), status


@auth_bp.route("/me", methods=["GET"])
@token_required
def me(current_user):
    return jsonify({
        "success": True,
        "data": {"usuario": current_user.to_dict()},
    }), 200


@auth_bp.route("/usuarios", methods=["POST"])
@token_required
@rol_requerido("admin")
def crear_usuario(current_user):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Body JSON requerido."}
        }), 400
    result, status = AuthService.crear_usuario_admin(data)
    return jsonify(result), status