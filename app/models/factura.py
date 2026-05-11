"""
Modelo Factura - Facturas de reservas
"""

import enum
from sqlalchemy import Numeric

from app import db
from app.utils.fecha_helper import ahora_colombia


class EstadoFactura(enum.Enum):
    pendiente = "Pendiente"
    emitida = "Emitida"
    pagada = "Pagada"
    anulada = "Anulada"


class Factura(db.Model):
    __tablename__ = "facturas"

    id = db.Column(db.Integer, primary_key=True)
    id_reserva = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id", name="fk_factura_reserva"),
        unique=True,
        nullable=False
    )
    fecha_emision = db.Column(
        db.DateTime,
        default=ahora_colombia,
        nullable=False
    )
    subtotal = db.Column(Numeric(10, 2), nullable=False)
    impuestos = db.Column(Numeric(10, 2), nullable=False)
    servicios_adicionales_total = db.Column(
        Numeric(10, 2),
        default=0,
        nullable=False
    )
    total = db.Column(Numeric(10, 2), nullable=False)
    estado = db.Column(
        db.Enum(EstadoFactura, native_enum=False),
        nullable=False
    )
    pdf_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False
    )

    # Relationships
    reserva = db.relationship("Reserva", back_populates="factura")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_reserva": self.id_reserva,
            "fecha_emision": self.fecha_emision.isoformat(),
            "subtotal": float(self.subtotal),
            "impuestos": float(self.impuestos),
            "servicios_adicionales_total": float(
                self.servicios_adicionales_total
            ),
            "total": float(self.total),
            "estado": self.estado.value,
            "pdf_path": self.pdf_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Factura {self.id} - {self.estado.value}>"
