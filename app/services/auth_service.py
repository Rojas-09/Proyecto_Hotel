"""
Auth Service - Lógica de negocio para autenticación
"""

from app import db
from app.models.usuario import Usuario, RolEnum
from app.models.huesped import Huesped
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

        rol = data.get("rol", "cliente").lower()
        if rol == "cliente":
            if not data.get("documento_id", "").strip():
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": (
                            "El campo 'documento_id' es requerido para clientes."
                        ),
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
            rol=rol,
        )
        usuario.password = data["password"]

        db.session.add(usuario)
        db.session.flush()

        if rol == "cliente":
            huesped = Huesped(
                id_usuario=usuario.id,
                documento_id=data["documento_id"].strip(),
                tipo_documento=data.get("tipo_documento", "CC").strip(),
                preferencias=data.get("preferencias", "").strip() or None,
            )
            db.session.add(huesped)

        db.session.commit()

        token = generar_token(
            usuario.id,
            usuario.email,
            usuario.rol.value if hasattr(usuario.rol, 'value') else usuario.rol
        )

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

        token = generar_token(
            usuario.id,
            usuario.email,
            usuario.rol.value if hasattr(usuario.rol, 'value') else usuario.rol
        )

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
        rol = data.get("rol", "cliente").lower()

        if rol not in roles_validos:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Rol inválido. Opciones: {', '.join(roles_validos)}",
                }
            }, 400

        if rol == "cliente":
            if not data.get("documento_id", "").strip():
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": (
                            "El campo 'documento_id' es requerido para clientes."
                        ),
                    }
                }, 400

        result, status = AuthService.registrar(data)
        if result["success"] and rol != "cliente":
            usuario = Usuario.query.filter_by(
                email=data["email"].lower()
            ).first()
            usuario.rol = RolEnum[rol]
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
                    "message": (
                        "Ya existe un administrador. "
                        "Usa el endpoint /usuarios con token de admin."
                    ),
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
            rol=RolEnum.admin,
        )
        usuario.password = data["password"]

        db.session.add(usuario)
        db.session.commit()

        token = generar_token(
            usuario.id,
            usuario.email,
            usuario.rol.value if hasattr(usuario.rol, 'value') else usuario.rol
        )

        return {
            "success": True,
            "data": {
                "usuario": usuario.to_dict(),
                "token": token,
            },
            "message": "Primer administrador creado exitosamente.",
        }, 201

    @staticmethod
    def editar_mi_perfil(current_user, data: dict) -> dict:
        """Cualquier usuario edita su propio perfil."""
        if "email" in data:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "No se puede cambiar el email.",
                }
            }, 400

        if "rol" in data:
            return {
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "No puedes cambiar tu propio rol.",
                }
            }, 400

        if "password" in data:
            if len(data["password"]) < 8:
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "La contraseña debe tener al menos 8 caracteres.",
                    }
                }, 400
            current_user.password = data["password"]

        if "nombre" in data:
            current_user.nombre = data["nombre"].strip()
        if "apellido" in data:
            current_user.apellido = data["apellido"].strip()
        if "telefono" in data:
            current_user.telefono = data["telefono"].strip() or None
        if "activo" in data:
            return {
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "No puedes cambiar tu propio estado.",
                }
            }, 400

        db.session.commit()

        return {
            "success": True,
            "data": {"usuario": current_user.to_dict()},
            "message": "Perfil actualizado correctamente.",
        }, 200

    @staticmethod
    def editar_usuario(usuario_id, current_user, data: dict) -> dict:
        """Editar usuario según permisos jerárquicos."""
        usuario = db.session.get(Usuario, usuario_id)
        if not usuario:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Usuario con id {usuario_id} no encontrado.",
                }
            }, 404

        # Admin puede cambiar email de cualquiera
        if "email" in data:
            rol_value = (
                current_user.rol.value
                if hasattr(current_user.rol, 'value')
                else current_user.rol
            )
            if rol_value != "admin":
                return {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Solo el admin puede cambiar el email.",
                    }
                }, 403
            nuevo_email = data["email"].strip().lower()
            if Usuario.query.filter(
                Usuario.email == nuevo_email,
                Usuario.id != usuario_id,
            ).first():
                return {
                    "success": False,
                    "error": {
                        "code": "CONFLICT",
                        "message": "El email ya está en uso.",
                    }
                }, 409
            usuario.email = nuevo_email

        # Verificar permisos según jerarquía
        rol_value = (
            current_user.rol.value
            if hasattr(current_user.rol, 'value')
            else current_user.rol
        )
        if rol_value == "cliente":
            return {
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "No tienes permiso para editar usuarios.",
                }
            }, 403

        # Gerente solo puede editar recepcionista y gerente
        rol_value = (
            current_user.rol.value
            if hasattr(current_user.rol, 'value')
            else current_user.rol
        )
        if rol_value == "gerente":
            if usuario.rol not in ("recepcionista", "gerente"):
                return {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Solo puedes editar recepcionistas y gerentes.",
                    }
                }, 403

        # No puede editarse a sí mismo en campo activo
        if usuario.id == current_user.id and "activo" in data and not data["activo"]:
            return {
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "No puedes desactivarte a ti mismo.",
                }
            }, 403

        # No puede cambiar su propio rol
        if usuario.id == current_user.id and "rol" in data:
            return {
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "No puedes cambiar tu propio rol.",
                }
            }, 403

        if "nombre" in data:
            usuario.nombre = data["nombre"].strip()
        if "apellido" in data:
            usuario.apellido = data["apellido"].strip()
        if "telefono" in data:
            usuario.telefono = data["telefono"].strip() or None
        if "activo" in data:
            # Solo admin puede desactivar usuarios
            rol_value = (
                current_user.rol.value
                if hasattr(current_user.rol, 'value')
                else current_user.rol
            )
            if rol_value != "admin":
                return {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Solo el admin puede activar/desactivar usuarios.",
                    }
                }, 403
            usuario.activo = data["activo"]

        if "rol" in data:
            roles_validos = {"admin", "recepcionista", "gerente", "cliente"}
            if data["rol"] not in roles_validos:
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": f"Rol inválido. Opciones: {', '.join(roles_validos)}",
                    }
                }, 400
            # Admin puede poner cualquier rol, gerente solo recepcionista/gerente
            if (
                (
                    current_user.rol.value
                    if hasattr(current_user.rol, 'value')
                    else current_user.rol
                )
                == "gerente"
                and data["rol"] not in ("recepcionista", "gerente")
            ):
                return {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": (
                            "Como gerente solo puedes asignar "
                            "rol recepcionista o gerente."
                        ),
                    }
                }, 403
            usuario.rol = data["rol"]

        if "password" in data:
            if len(data["password"]) < 8:
                return {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "La contraseña debe tener al menos 8 caracteres.",
                    }
                }, 400
            usuario.password = data["password"]

        db.session.commit()

        return {
            "success": True,
            "data": {"usuario": usuario.to_dict()},
            "message": "Usuario actualizado correctamente.",
        }, 200
