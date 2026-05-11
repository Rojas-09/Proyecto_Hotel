"""
JWT Helper - Generación y validación de tokens
Decorador @token_required para proteger endpoints
"""

import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, current_app, jsonify


def generar_token(user_id: int, email: str, rol: str) -> str:
    expiration_hours = current_app.config.get("JWT_EXPIRATION_HOURS", 24)
    payload = {
        "user_id": user_id,
        "email": email,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expiration_hours),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decodificar_token(token: str) -> dict:
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Token de autenticación requerido.",
                }
            }), 401

        try:
            payload = decodificar_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "El token ha expirado. Inicia sesión nuevamente.",
                }
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Token inválido.",
                }
            }), 401

        from app.models.usuario import Usuario
        current_user = Usuario.query.get(payload["user_id"])

        if not current_user or not current_user.activo:
            return jsonify({
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Usuario no encontrado o inactivo.",
                }
            }), 401

        return f(current_user, *args, **kwargs)

    return decorated


def rol_requerido(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            user_rol = (
                current_user.rol.value
                if hasattr(current_user.rol, 'value')
                else current_user.rol
            )
            if user_rol not in roles:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Acceso restringido. Roles permitidos: {', '.join(roles)}.",
                    }
                }), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator