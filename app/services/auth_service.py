"""
Auth Service - Lógica de negocio para autenticación
"""

from sqlalchemy import select

from app import db
from app.models.usuario import Usuario, RolEnum
from app.models.huesped import Huesped
from app.utils.jwt_helper import generar_token


class AuthService:

    @staticmethod
    def _rol_normalizado(usuario) -> str:
        return (
            usuario.rol.value
            if hasattr(usuario.rol, 'value')
            else usuario.rol
        )

    @staticmethod
    def _nivel_rol(rol: str) -> int:
        niveles = {
            "cliente": 0,
            "recepcionista": 1,
            "gerente": 2,
            "admin": 3,
        }
        return niveles.get(rol, -1)

    @staticmethod
    def _puede_gestionar_usuario(current_user, usuario) -> bool:
        rol_actual = AuthService._rol_normalizado(current_user)
        if rol_actual == "admin":
            return True
        if current_user.id == usuario.id:
            return True
        return AuthService._nivel_rol(rol_actual) > AuthService._nivel_rol(
            AuthService._rol_normalizado(usuario)
        )

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

        if db.session.execute(
            select(Usuario).filter_by(email=email)
        ).scalar_one_or_none():
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

        usuario = db.session.execute(
            select(Usuario).filter_by(email=email, activo=True)
        ).scalar_one_or_none()

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
            return AuthService.registrar(data)

        usuario = Usuario(
            nombre=data["nombre"].strip(),
            apellido=data.get("apellido", "").strip(),
            email=data["email"].lower().strip(),
            telefono=data.get("telefono", "").strip(),
            rol=RolEnum[rol],
        )
        usuario.password = data["password"]
        db.session.add(usuario)
        db.session.commit()
        return {
            "success": True,
            "data": {"usuario": usuario.to_dict()},
            "mensaje": f"Usuario {rol} creado correctamente."
        }, 201

    @staticmethod
    def crear_primer_admin(data: dict) -> dict:
        """Crea el primer admin. Solo funciona si no hay admins en la DB."""
        admin_existe = db.session.execute(
            select(Usuario).filter_by(rol="admin", activo=True)
        ).scalar_one_or_none()
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
        if (
            "activo" in data
            and data["activo"] is False
            and usuario_id == current_user.id
        ):
            return {
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "No puedes desactivarte a ti mismo.",
                }
            }, 403

        usuario = db.session.get(Usuario, usuario_id)
        if not usuario:
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Usuario con id {usuario_id} no encontrado.",
                }
            }, 404

        rol_actual = AuthService._rol_normalizado(current_user)

        if not AuthService._puede_gestionar_usuario(current_user, usuario):
            return {
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "No tienes permiso para editar este usuario.",
                }
            }, 403

        # El email solo puede cambiarlo el admin
        if "email" in data:
            if rol_actual != "admin":
                return {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Solo el admin puede cambiar el email.",
                    }
                }, 403
            nuevo_email = data["email"].strip().lower()
            if db.session.execute(
                select(Usuario).filter(
                    Usuario.email == nuevo_email,
                    Usuario.id != usuario_id,
                )
            ).scalar_one_or_none():
                return {
                    "success": False,
                    "error": {
                        "code": "CONFLICT",
                        "message": "El email ya está en uso.",
                    }
                }, 409
            usuario.email = nuevo_email

        if "nombre" in data:
            usuario.nombre = data["nombre"].strip()
        if "apellido" in data:
            usuario.apellido = data["apellido"].strip()
        if "telefono" in data:
            usuario.telefono = data["telefono"].strip() or None

        if "activo" in data:
            if rol_actual != "admin":
                return {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Solo el admin puede activar o desactivar usuarios.",
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
            if usuario.id == current_user.id:
                return {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "No puedes cambiar tu propio rol.",
                    }
                }, 403
            if rol_actual == "gerente" and data["rol"] == "admin":
                return {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Como gerente no puedes asignar rol admin.",
                    }
                }, 403
            if rol_actual == "recepcionista" and data["rol"] in ("admin", "gerente"):
                return {
                    "success": False,
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Como recepcionista no puedes asignar roles superiores.",
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

    @staticmethod
    def listar_usuarios() -> list:
        usuarios = db.session.execute(
            select(Usuario).order_by(Usuario.created_at.desc())
        ).scalars().all()
        return [u.to_dict() for u in usuarios]

    @staticmethod
    def obtener_usuario(usuario_id: int) -> dict:
        usuario = db.session.get(Usuario, usuario_id)
        if not usuario:
            raise LookupError(f"Usuario con id {usuario_id} no encontrado.")
        return usuario.to_dict()

    @staticmethod
    def eliminar_usuario(usuario_id: int) -> dict:
        usuario = db.session.get(Usuario, usuario_id)
        if not usuario:
            raise LookupError(f"Usuario con id {usuario_id} no encontrado.")
        email = usuario.email
        usuario.activo = False
        db.session.commit()
        return {"email": email, "id": usuario_id}
