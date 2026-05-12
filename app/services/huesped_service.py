"""
Huesped Service - Lógica de negocio para huéspedes
"""

from sqlalchemy import or_

from app import db
from app.models.huesped import Huesped
from app.models.usuario import Usuario


def obtener_todos():
    """Obtiene todos los huéspedes."""
    huespedes = Huesped.query.order_by(Huesped.created_at.desc()).all()
    return [h.to_dict() for h in huespedes]


def obtener_por_id(huesped_id):
    """Obtiene un huésped por ID."""
    huesped = db.session.get(Huesped, huesped_id)
    if not huesped:
        raise LookupError(
            f"Huésped con id {huesped_id} no encontrado."
        )
    return huesped.to_dict()


def obtener_por_usuario(usuario_id):
    """Obtiene un huésped por ID de usuario."""
    huesped = Huesped.query.filter_by(id_usuario=usuario_id).first()
    if not huesped:
        raise LookupError(
            f"Huésped para usuario {usuario_id} no encontrado."
        )
    return huesped.to_dict()


def actualizar(huesped_id, datos: dict):
    """Actualiza un huésped."""
    huesped = db.session.get(Huesped, huesped_id)
    if not huesped:
        raise LookupError(
            f"Huésped con id {huesped_id} no encontrado."
        )

    if "documento_id" in datos:
        huesped.documento_id = datos["documento_id"].strip()

    if "tipo_documento" in datos:
        huesped.tipo_documento = datos["tipo_documento"].strip()

    if "preferencias" in datos:
        huesped.preferencias = (
            datos["preferencias"].strip() or None
        )

    db.session.commit()
    return huesped.to_dict()


def buscar(query: str):
    """Busca huéspedes por nombre, apellido, email o documento_id."""
    if not query or not query.strip():
        raise ValueError("Debe proporcionar un término de búsqueda.")

    q = query.strip().lower()
    resultados = Huesped.query.join(Usuario).filter(
        or_(
            db.func.lower(Usuario.nombre).like(f"%{q}%"),
            db.func.lower(Usuario.apellido).like(f"%{q}%"),
            db.func.lower(Usuario.email).like(f"%{q}%"),
            db.func.lower(Huesped.documento_id).like(f"%{q}%"),
        )
    ).order_by(Huesped.created_at.desc()).all()

    return [h.to_dict() for h in resultados]
