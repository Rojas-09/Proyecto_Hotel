"""
Modelo Reserva - Reservas de habitaciones
"""

import enum
from sqlalchemy import Numeric

from app import db
from app.utils.fecha_helper import ahora_colombia


class EstadoReserva(enum.Enum):
    pendiente = "Pendiente"
    confirmada = "Confirmada"
    ocupada = "Ocupada"
    completada = "Completada"
    cancelada = "Cancelada"


class Reserva(db.Model):
    __tablename__ = "reservas"

    id = db.Column(db.Integer, primary_key=True)
    id_huesped = db.Column(
        db.Integer,
        db.ForeignKey("huespedes.id", name="fk_reserva_huesped"),
        nullable=False
    )
    id_habitacion = db.Column(
        db.Integer,
        db.ForeignKey("habitaciones.id", name="fk_reserva_habitacion"),
        nullable=False
    )
    fecha_reserva = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    fecha_entrada = db.Column(db.Date, nullable=False)
    fecha_salida = db.Column(db.Date, nullable=False)
    noches = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(Numeric(10, 2), nullable=False)
    impuestos = db.Column(Numeric(10, 2), nullable=False)
    total = db.Column(Numeric(10, 2), nullable=False)
    estado = db.Column(
        db.Enum(EstadoReserva, native_enum=False),
        nullable=False,
        default=EstadoReserva.pendiente
    )
    motivo_cancelacion = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False
    )

    # Relationships
    huesped = db.relationship("Huesped", back_populates="reservas")
    habitacion = db.relationship("Habitacion", back_populates="reservas")
    checkin_checkout = db.relationship(
        "CheckInCheckOut",
        back_populates="reserva",
        uselist=False
    )
    pagos = db.relationship("Pago", back_populates="reserva")
    factura = db.relationship(
        "Factura",
        back_populates="reserva",
        uselist=False
    )
    notificaciones = db.relationship("Notificacion", back_populates="reserva")
    servicios_adicionales = db.relationship(
        "ServicioAdicional",
        back_populates="reserva"
    )
    puntos_fidelidad = db.relationship(
        "PuntosFidelidad",
        back_populates="reserva",
        uselist=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_huesped": self.id_huesped,
            "id_habitacion": self.id_habitacion,
            "fecha_reserva": self.fecha_reserva.isoformat(),
            "fecha_entrada": self.fecha_entrada.isoformat(),
            "fecha_salida": self.fecha_salida.isoformat(),
            "noches": self.noches,
            "subtotal": float(self.subtotal),
            "impuestos": float(self.impuestos),
            "total": float(self.total),
            "estado": self.estado.value,
            "motivo_cancelacion": self.motivo_cancelacion,
            "huesped_nombre": (
                f"{self.huesped.usuario.nombre} "
                f"{self.huesped.usuario.apellido}"
                if self.huesped and self.huesped.usuario else None
            ),
            "huesped_email": (
                self.huesped.usuario.email
                if self.huesped and self.huesped.usuario else None
            ),
            "huesped_documento": (
                self.huesped.documento_id if self.huesped else None
            ),
            "habitacion_numero": (
                self.habitacion.numero if self.habitacion else None
            ),
            "habitacion_tipo": (
                self.habitacion.tipo.value if self.habitacion else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Reserva {self.id} - {self.estado.value}>"
