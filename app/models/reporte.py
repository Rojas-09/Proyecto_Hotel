"""
Modelo ReporteGenerado - Historial de reportes generados
"""

from app import db
from app.utils.fecha_helper import ahora_colombia


class ReporteGenerado(db.Model):
    __tablename__ = "reportes_generados"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # ocupacion, ingresos, estadisticas
    formato = db.Column(db.String(10), nullable=False)  # xlsx, pdf
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    archivo_path = db.Column(db.String(500), nullable=False)
    archivo_nombre = db.Column(db.String(255), nullable=False)
    creado_por = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", name="fk_reporte_usuario"),
        nullable=False
    )
    resumen = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=ahora_colombia, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=ahora_colombia,
        onupdate=ahora_colombia,
        nullable=False
    )

    # Relationships
    usuario = db.relationship("Usuario", back_populates="reportes_generados")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "formato": self.formato,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "archivo_path": self.archivo_path,
            "archivo_nombre": self.archivo_nombre,
            "creado_por": self.creado_por,
            "resumen": self.resumen,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<ReporteGenerado {self.id} - {self.tipo} - {self.formato}>"
