import enum

from sqlalchemy import Numeric

from app import db
from app.utils.fecha_helper import ahora_colombia


class TipoHabitacion(enum.Enum):
    simple = "Simple"
    doble = "Doble"
    suite = "Suite"
    deluxe = "Deluxe"


class EstadoHabitacion(enum.Enum):
    disponible = "Disponible"
    ocupada = "Ocupada"
    mantenimiento = "Mantenimiento"


class Habitacion(db.Model):
    __tablename__ = "habitaciones"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    tipo = db.Column(
        db.Enum(TipoHabitacion, native_enum=False),
        nullable=False
    )
    descripcion = db.Column(db.Text, nullable=True)
    precio_noche = db.Column(Numeric(10, 2), nullable=False)
    capacidad = db.Column(db.Integer, nullable=False)
    piso = db.Column(db.Integer, nullable=False, default=1)
    estado = db.Column(
        db.Enum(EstadoHabitacion, native_enum=False),
        nullable=False,
        default=EstadoHabitacion.disponible
    )
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "tipo": self.tipo.value,
            "descripcion": self.descripcion,
            "precio_noche": float(self.precio_noche),
            "capacidad": self.capacidad,
            "piso": self.piso,
            "estado": self.estado.value,
            "activo": self.activo,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Habitacion {self.numero} - {self.tipo.value}>"