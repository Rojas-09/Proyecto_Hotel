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

from app.services.auth_service import AuthService
from app.utils.error_helper import handle_service_error
from app.utils.jwt_helper import token_required, rol_requerido

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register-admin", methods=["POST"])
def register_admin():
    """Crea el primer administrador. Solo funciona si no hay admins en la DB."""
    from flask import current_app

    if not current_app.config.get("ADMIN_BOOTSTRAP_ENABLED", False):
        return jsonify({
            "success": False,
            "error": {"code": "FORBIDDEN", "message": "Endpoint deshabilitado."}
        }), 403

    secret = current_app.config.get("ADMIN_BOOTSTRAP_SECRET", "")
    if secret and request.headers.get("X-Bootstrap-Secret") != secret:
        return jsonify({
            "success": False,
            "error": {"code": "UNAUTHORIZED", "message": "No autorizado."}
        }), 401

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
def editar_usuario(current_user, usuario_id):
    """Editar un usuario según jerarquía de roles."""
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
    try:
        usuarios = AuthService.listar_usuarios()
        return jsonify({
            "success": True,
            "data": usuarios,
            "total": len(usuarios),
            "mensaje": "Usuarios obtenidos correctamente."
        }), 200
    except Exception as e:
        return handle_service_error(e, 500)


@auth_bp.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
@token_required
@rol_requerido("admin")
def eliminar_usuario(current_user, usuario_id):
    if usuario_id == current_user.id:
        return jsonify({
            "success": False,
            "error": {"code": "FORBIDDEN", "message": "No puedes eliminarte a ti mismo."}
        }), 403

    try:
        resultado = AuthService.eliminar_usuario(usuario_id)
        return jsonify({
            "success": True,
            "data": None,
            "mensaje": f"Usuario {resultado['email']} eliminado correctamente."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except Exception as e:
        return handle_service_error(e, 500)


@auth_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
@token_required
def obtener_usuario(current_user, usuario_id):
    try:
        usuario = AuthService.obtener_usuario(usuario_id)
        return jsonify({
            "success": True,
            "data": {"usuario": usuario}
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except Exception as e:
        return handle_service_error(e, 500)


@auth_bp.route("/me", methods=["DELETE"])
@token_required
def eliminar_mi_cuenta(current_user):
    """Eliminar (soft-delete) la propia cuenta del usuario."""
    try:
        AuthService.eliminar_usuario(current_user.id)
        return jsonify({
            "success": True,
            "data": None,
            "mensaje": "Cuenta desactivada correctamente."
        }), 200
    except LookupError:
        return jsonify({
            "success": False,
            "error": {"code": "NOT_FOUND", "message": "Usuario no encontrado."}
        }), 404
    except Exception as e:
        return handle_service_error(e, 500)
