"""
Modelo CheckInCheckOut - Registro de entrada y salida
"""

from app import db
from app.utils.fecha_helper import ahora_colombia


class CheckInCheckOut(db.Model):
    __tablename__ = "checkin_checkout"

    id = db.Column(db.Integer, primary_key=True)
    id_reserva = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id", name="fk_checkin_reserva"),
        unique=True,
        nullable=False
    )
    fecha_checkin = db.Column(db.DateTime, nullable=True)
    fecha_checkout = db.Column(db.DateTime, nullable=True)
    realizado_por = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", name="fk_checkin_usuario"),
        nullable=True
    )
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False
    )

    # Relationships
    reserva = db.relationship("Reserva", back_populates="checkin_checkout")
    usuario = db.relationship("Usuario", foreign_keys=[realizado_por])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_reserva": self.id_reserva,
            "fecha_checkin": (
                self.fecha_checkin.isoformat() if self.fecha_checkin else None
            ),
            "fecha_checkout": (
                self.fecha_checkout.isoformat() if self.fecha_checkout else None
            ),
            "realizado_por": self.realizado_por,
            "usuario_nombre": (
                f"{self.usuario.nombre} {self.usuario.apellido}"
                if self.usuario else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<CheckInCheckOut Reserva={self.id_reserva}>"
