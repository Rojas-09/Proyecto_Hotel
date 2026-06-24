"""
Modelo RefreshToken — Tokens de refresco revocables (RF-13 M2)
"""
import hashlib
import uuid
from datetime import timedelta

from app import db
from app.utils.fecha_helper import ahora_colombia


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", name="fk_refresh_token_usuario"),
        nullable=False,
    )
    token_hash = db.Column(db.String(128), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False,
    )

    usuario = db.relationship("Usuario", foreign_keys=[id_usuario])

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _generar_token() -> str:
        return uuid.uuid4().hex

    @classmethod
    def crear(cls, id_usuario: int, dias: int = 7):
        token_plano = cls._generar_token()
        token_hash = cls._hash(token_plano)
        expires_at = ahora_colombia() + timedelta(days=dias)
        rt = cls(
            id_usuario=id_usuario,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.session.add(rt)
        db.session.flush()
        return token_plano, rt

    @classmethod
    def verificar(cls, token_plano: str):
        token_hash = cls._hash(token_plano)
        ahora = ahora_colombia()
        return db.session.execute(
            db.select(cls).filter(
                cls.token_hash == token_hash,
                cls.revoked.is_(False),
                cls.expires_at > ahora,
            )
        ).scalar_one_or_none()

    def revocar(self):
        self.revoked = True
        self.updated_at = ahora_colombia()

    def to_dict(self):
        return {
            "id": self.id,
            "id_usuario": self.id_usuario,
            "expires_at": self.expires_at.isoformat(),
            "revoked": self.revoked,
            "created_at": self.created_at.isoformat(),
        }
