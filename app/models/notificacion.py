"""
Modelo Notificacion - Notificaciones de reservas
"""

import enum

from app import db
from app.utils.fecha_helper import ahora_colombia


class TipoNotificacion(enum.Enum):
    confirmacion_reserva = "ConfirmacionReserva"
    recordatorio = "Recordatorio"
    cancelacion = "Cancelacion"
    factura = "Factura"


class Notificacion(db.Model):
    __tablename__ = "notificaciones"

    id = db.Column(db.Integer, primary_key=True)
    id_reserva = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id", name="fk_notificacion_reserva"),
        nullable=False
    )
    tipo = db.Column(
        db.Enum(TipoNotificacion, native_enum=False),
        nullable=False
    )
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, nullable=True)
    enviado = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False
    )

    # Relationships
    reserva = db.relationship("Reserva", back_populates="notificaciones")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_reserva": self.id_reserva,
            "tipo": self.tipo.value,
            "mensaje": self.mensaje,
            "fecha_envio": (
                self.fecha_envio.isoformat() if self.fecha_envio else None
            ),
            "enviado": self.enviado,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return (
            f"<Notificacion {self.id} - {self.tipo.value} "
            f"({'Enviado' if self.enviado else 'Pendiente'})>"
        )
