"""
Modelo Usuario - Entidad central de autenticación y roles
"""

import enum
import bcrypt
from flask import current_app  # noqa: F401

from app import db
from app.utils.fecha_helper import ahora_colombia


class RolEnum(enum.Enum):
    admin = "admin"
    recepcionista = "recepcionista"
    gerente = "gerente"
    cliente = "cliente"


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    _password_hash = db.Column("password_hash", db.String(255))
    telefono = db.Column(db.String(20), nullable=True)
    rol = db.Column(
        db.Enum(RolEnum, native_enum=False),
        nullable=False,
        default=RolEnum.cliente
    )
    puntos_fidelizacion = db.Column(db.Integer, default=0, nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=ahora_colombia, onupdate=ahora_colombia,
        nullable=False
    )

    # Relationships
    huesped = db.relationship(
        "Huesped",
        back_populates="usuario",
        uselist=False
    )

    @property
    def password(self):
        raise AttributeError("La contraseña no es legible directamente.")

    @password.setter
    def password(self, plain_text: str):
        rounds = current_app.config.get("BCRYPT_LOG_ROUNDS", 12)
        self._password_hash = bcrypt.hashpw(
            plain_text.encode("utf-8"),
            bcrypt.gensalt(rounds=rounds),
        ).decode("utf-8")

    def verificar_password(self, plain_text: str) -> bool:
        if not self._password_hash:
            return False
        return bcrypt.checkpw(
            plain_text.encode("utf-8"),
            self._password_hash.encode("utf-8"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "telefono": self.telefono,
            "rol": self.rol.value,
            "puntos_fidelizacion": self.puntos_fidelizacion,
            "activo": self.activo,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Usuario {self.email} [{self.rol.value}]>"
