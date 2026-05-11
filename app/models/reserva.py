import enum

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
    id_cliente = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", name="fk_reserva_cliente"),
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
    total = db.Column(db.Numeric(10, 2), nullable=False)
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

    cliente = db.relationship(
        "Usuario",
        foreign_keys=[id_cliente],
        backref="reservas"
    )
    habitacion = db.relationship(
        "Habitacion",
        foreign_keys=[id_habitacion],
        backref="reservas"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "id_cliente": self.id_cliente,
            "id_habitacion": self.id_habitacion,
            "fecha_reserva": self.fecha_reserva.isoformat(),
            "fecha_entrada": self.fecha_entrada.isoformat(),
            "fecha_salida": self.fecha_salida.isoformat(),
            "noches": self.noches,
            "total": float(self.total),
            "estado": self.estado.value,
            "motivo_cancelacion": self.motivo_cancelacion,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "cliente_nombre": self.cliente.nombre + " " + self.cliente.apellido,
            "cliente_email": self.cliente.email,
            "habitacion_numero": self.habitacion.numero,
            "habitacion_tipo": self.habitacion.tipo.value,
        }

    def __repr__(self):
        return f"<Reserva {self.id} - {self.estado.value}>"