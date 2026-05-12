"""
Auth Controller - Endpoints de autenticación
POST /api/v1/auth/register        → Registro de cliente (requiere documento_id)
POST /api/v1/auth/register-admin  → Crear primer admin (solo si no hay admins)
POST /api/v1/auth/login           → Login + JWT
GET  /api/v1/auth/me              → Datos del usuario autenticado
PUT  /api/v1/auth/me              → Editar mi perfil (cualquier usuario)
GET  /api/v1/auth/usuarios        → Listar todos los usuarios (solo admin)
POST /api/v1/auth/usuarios        → Crear cualquier rol (solo admin)
PUT  /api/v1/auth/usuarios/<id>   → Editar usuario (admin/gerente)
DELETE /api/v1/auth/usuarios/<id> → Soft delete usuario (solo admin)
"""

from flask import Blueprint, request, jsonify

from app import db
from app.models.usuario import Usuario
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


@auth_bp.route("/me", methods=["PUT"])
@token_required
def editar_mi_perfil(current_user):
    """Editar mi propio perfil."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Body JSON requerido."}
        }), 400
    result, status = AuthService.editar_mi_perfil(current_user, data)
    return jsonify(result), status


@auth_bp.route("/usuarios/<int:usuario_id>", methods=["PUT"])
@token_required
@rol_requerido("admin", "gerente")
def editar_usuario(current_user, usuario_id):
    """Admin edita cualquier usuario."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": "Body JSON requerido."}
        }), 400
    result, status = AuthService.editar_usuario(usuario_id, current_user, data)
    return jsonify(result), status


@auth_bp.route("/usuarios", methods=["GET"])
@token_required
@rol_requerido("admin")
def listar_usuarios(current_user):
    """Listar todos los usuarios (solo admin)."""
    usuarios = Usuario.query.order_by(Usuario.created_at.desc()).all()
    return jsonify({
        "success": True,
        "data": [u.to_dict() for u in usuarios],
        "total": len(usuarios),
        "mensaje": "Usuarios obtenidos correctamente."
    }), 200


@auth_bp.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
@token_required
@rol_requerido("admin")
def eliminar_usuario(current_user, usuario_id):
    """Soft delete de usuario (solo admin, no puede eliminarse a sí mismo)."""
    if usuario_id == current_user.id:
        return jsonify({
            "success": False,
            "error": {"code": "FORBIDDEN", "message": "No puedes eliminarte a ti mismo."}
        }), 403

    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return jsonify({
            "success": False,
            "error": {"code": "NOT_FOUND", "message": f"Usuario con id {usuario_id} no encontrado."}
        }), 404

    usuario.activo = False
    db.session.commit()

    return jsonify({
        "success": True,
        "data": None,
        "mensaje": f"Usuario {usuario.email} eliminado correctamente."
    }), 200
