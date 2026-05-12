"""
Modelo Huésped - Información del cliente en una reserva
"""

from app import db
from app.utils.fecha_helper import ahora_colombia


class Huesped(db.Model):
    __tablename__ = "huespedes"

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", name="fk_huesped_usuario"),
        unique=True,
        nullable=False
    )
    documento_id = db.Column(db.String(20), nullable=False)
    tipo_documento = db.Column(db.String(20), nullable=False, default="CC")
    preferencias = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False
    )

    # Relationships
    usuario = db.relationship("Usuario", back_populates="huesped")
    reservas = db.relationship("Reserva", back_populates="huesped")
    puntos_fidelidad = db.relationship(
        "PuntosFidelidad",
        back_populates="huesped",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        usuario_data = self.usuario.to_dict() if self.usuario else {}
        return {
            "id": self.id,
            "id_usuario": self.id_usuario,
            "documento_id": self.documento_id,
            "tipo_documento": self.tipo_documento,
            "preferencias": self.preferencias,
            "nombre": usuario_data.get("nombre"),
            "apellido": usuario_data.get("apellido"),
            "email": usuario_data.get("email"),
            "telefono": usuario_data.get("telefono"),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return (
            f"<Huesped {self.documento_id} "
            f"({self.usuario.nombre if self.usuario else 'Sin usuario'})>"
        )
