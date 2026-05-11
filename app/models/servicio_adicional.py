"""
Modelo ServicioAdicional - Servicios adicionales en reservas
"""

import enum
from sqlalchemy import Numeric

from app import db
from app.utils.fecha_helper import ahora_colombia


class TipoServicio(enum.Enum):
    comedor = "Comedor"
    spa = "Spa"
    lavanderia = "Lavanderia"
    otro = "Otro"


class ServicioAdicional(db.Model):
    __tablename__ = "servicios_adicionales"

    id = db.Column(db.Integer, primary_key=True)
    id_reserva = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id", name="fk_servicio_reserva"),
        nullable=False
    )
    tipo = db.Column(
        db.Enum(TipoServicio, native_enum=False),
        nullable=False
    )
    descripcion = db.Column(db.String(255), nullable=False)
    costo = db.Column(Numeric(10, 2), nullable=False)
    fecha_hora = db.Column(
        db.DateTime,
        default=ahora_colombia,
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False
    )

    # Relationships
    reserva = db.relationship("Reserva", back_populates="servicios_adicionales")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_reserva": self.id_reserva,
            "tipo": self.tipo.value,
            "descripcion": self.descripcion,
            "costo": float(self.costo),
            "fecha_hora": self.fecha_hora.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return (
            f"<ServicioAdicional {self.id} - {self.tipo.value} "
            f"({self.descripcion[:30]})>"
        )
