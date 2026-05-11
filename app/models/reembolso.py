"""
Modelo Reembolso - Reembolsos de pagos
"""

import enum
from sqlalchemy import Numeric

from app import db
from app.utils.fecha_helper import ahora_colombia


class EstadoReembolso(enum.Enum):
    solicitado = "Solicitado"
    procesado = "Procesado"
    rechazado = "Rechazado"


class Reembolso(db.Model):
    __tablename__ = "reembolsos"

    id = db.Column(db.Integer, primary_key=True)
    id_pago = db.Column(
        db.Integer,
        db.ForeignKey("pagos.id", name="fk_reembolso_pago"),
        unique=True,
        nullable=False
    )
    fecha = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    monto = db.Column(Numeric(10, 2), nullable=False)
    motivo = db.Column(db.String(255), nullable=False)
    estado = db.Column(
        db.Enum(EstadoReembolso, native_enum=False),
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
    pago = db.relationship("Pago", back_populates="reembolso")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_pago": self.id_pago,
            "fecha": self.fecha.isoformat(),
            "monto": float(self.monto),
            "motivo": self.motivo,
            "estado": self.estado.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return (
            f"<Reembolso {self.id} - {self.estado.value} "
            f"({self.motivo[:30]})>"
        )
