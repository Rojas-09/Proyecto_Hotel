"""
Modelo PuntosFidelidad - Registro de puntos ganados por huéspedes (RF-12)
"""

from app import db
from app.utils.fecha_helper import ahora_colombia


class PuntosFidelidad(db.Model):
    __tablename__ = "puntos_fidelidad"

    id = db.Column(db.Integer, primary_key=True)
    id_huesped = db.Column(
        db.Integer,
        db.ForeignKey("huespedes.id", name="fk_puntos_huesped"),
        nullable=False
    )
    id_reserva = db.Column(
        db.Integer,
        db.ForeignKey("reservas.id", name="fk_puntos_reserva"),
        nullable=True
    )
    puntos = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    concepto = db.Column(db.String(200), nullable=False)

    # Relationships
    huesped = db.relationship("Huesped", back_populates="puntos_fidelidad")
    reserva = db.relationship("Reserva", back_populates="puntos_fidelidad")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_huesped": self.id_huesped,
            "id_reserva": self.id_reserva,
            "puntos": self.puntos,
            "fecha": self.fecha.isoformat(),
            "concepto": self.concepto,
        }

    def __repr__(self):
        return f"<PuntosFidelidad {self.id} - {self.puntos} pts para Huesped {self.id_huesped}>"
