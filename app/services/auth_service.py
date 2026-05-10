"""
Auth Service - Lógica de negocio para autenticación
"""

from app import db
from app.models.usuario import Usuario
from app.utils.jwt_helper import generar_token


class AuthService:

    @staticmethod
    def registrar(data: dict) -> dict:
        campos = ["nombre", "apellido", "email", "password"]
        for campo in campos:
            if not data.get(campo, "").strip():
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": f"El campo '{campo}' es requerido.",
                    }
                }, 400

        email = data["email"].strip().lower()

        if Usuario.query.filter_by(email=email).first():
            return {
                "success": False,
                "error": {
                    "code": "CONFLICT",
                    "message": "Ya existe una cuenta con ese correo electrónico.",
                }
            }, 409

        if len(data["password"]) < 8:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "La contraseña debe tener al menos 8 caracteres.",
                }
            }, 400

        usuario = Usuario(
            nombre=data["nombre"].strip(),
            apellido=data["apellido"].strip(),
            email=email,
            telefono=data.get("telefono", "").strip() or None,
            rol="cliente",
        )
        usuario.password = data["password"]

        db.session.add(usuario)
        db.session.commit()

        token = generar_token(usuario.id, usuario.email, usuario.rol)

        return {
            "success": True,
            "data": {
                "usuario": usuario.to_dict(),
                "token": token,
            },
            "message": "Cuenta creada exitosamente.",
        }, 201

    @staticmethod
    def login(data: dict) -> dict:
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Email y contraseña son requeridos.",
                }
            }, 400

        usuario = Usuario.query.filter_by(email=email, activo=True).first()

        if not usuario or not usuario.verificar_password(password):
            return {
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Credenciales incorrectas.",
                }
            }, 401

        token = generar_token(usuario.id, usuario.email, usuario.rol)

        return {
            "success": True,
            "data": {
                "usuario": usuario.to_dict(),
                "token": token,
            },
            "message": "Sesión iniciada correctamente.",
        }, 200

    @staticmethod
    def crear_usuario_admin(data: dict) -> dict:
        roles_validos = {"admin", "recepcionista", "gerente", "cliente"}
        rol = data.get("rol", "cliente")

        if rol not in roles_validos:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Rol inválido. Opciones: {', '.join(roles_validos)}",
                }
            }, 400

        result, status = AuthService.registrar(data)
        if result["success"] and rol != "cliente":
            usuario = Usuario.query.filter_by(email=data["email"].lower()).first()
            usuario.rol = rol
            db.session.commit()
            result["data"]["usuario"] = usuario.to_dict()

        return result, status

    @staticmethod
    def crear_primer_admin(data: dict) -> dict:
        """Crea el primer admin. Solo funciona si no hay admins en la DB."""
        admin_existe = Usuario.query.filter_by(rol="admin", activo=True).first()
        if admin_existe:
            return {
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Ya existe un administrador. Usa el endpoint /usuarios con token de admin.",
                }
            }, 403

        campos = ["nombre", "apellido", "email", "password"]
        for campo in campos:
            if not data.get(campo, "").strip():
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": f"El campo '{campo}' es requerido.",
                    }
                }, 400

        if len(data["password"]) < 8:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "La contraseña debe tener al menos 8 caracteres.",
                }
            }, 400

        email = data["email"].strip().lower()

        usuario = Usuario(
            nombre=data["nombre"].strip(),
            apellido=data["apellido"].strip(),
            email=email,
            telefono=data.get("telefono", "").strip() or None,
            rol="admin",
        )
        usuario.password = data["password"]

        db.session.add(usuario)
        db.session.commit()

        token = generar_token(usuario.id, usuario.email, usuario.rol)

        return {
            "success": True,
            "data": {
                "usuario": usuario.to_dict(),
                "token": token,
            },
            "message": "Primer administrador creado exitosamente.",
        }, 201