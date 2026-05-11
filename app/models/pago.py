"""
Modelo Pago - Pagos de reservas
"""

import enum
from sqlalchemy import Numeric

from app import db
from app.utils.fecha_helper import ahora_colombia


class MetodoPago(enum.Enum):
    tarjeta = "Tarjeta"
    efectivo = "Efectivo"
    transferencia = "Transferencia"


class TipoPago(enum.Enum):
    garantia = "Garantia"
    liquidacion = "Liquidacion"


class EstadoPago(enum.Enum):
    pendiente = "Pendiente"
    aprobado = "Aprobado"
    rechazado = "Rechazado"
    reembolsado = "Reembolsado"


class Pago(db.Model):
    __tablename__ = "pagos"

    id = db.Column(db.Integer, primary_key=True)
    id_reserva = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id", name="fk_pago_reserva"),
        nullable=False
    )
    fecha = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    monto = db.Column(Numeric(10, 2), nullable=False)
    metodo = db.Column(
        db.Enum(MetodoPago, native_enum=False),
        nullable=False
    )
    tipo = db.Column(
        db.Enum(TipoPago, native_enum=False),
        nullable=False
    )
    estado = db.Column(
        db.Enum(EstadoPago, native_enum=False),
        nullable=False
    )
    referencia_externa = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False
    )

    # Relationships
    reserva = db.relationship("Reserva", back_populates="pagos")
    reembolso = db.relationship(
        "Reembolso",
        back_populates="pago",
        uselist=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_reserva": self.id_reserva,
            "fecha": self.fecha.isoformat(),
            "monto": float(self.monto),
            "metodo": self.metodo.value,
            "tipo": self.tipo.value,
            "estado": self.estado.value,
            "referencia_externa": self.referencia_externa,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return (
            f"<Pago {self.id} - {self.estado.value} "
            f"({self.metodo.value})>"
        )
