"""
Huesped Service - Lógica de negocio para huéspedes
"""

from sqlalchemy import or_, select

from app import db
from app.models.huesped import Huesped
from app.models.usuario import Usuario


def obtener_todos():
    """Obtiene todos los huéspedes."""
    huespedes = db.session.execute(
        select(Huesped).order_by(Huesped.created_at.desc())
    ).scalars().all()
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
    huesped = db.session.execute(
        select(Huesped).filter_by(id_usuario=usuario_id)
    ).scalar_one_or_none()
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
    resultados = db.session.execute(
        select(Huesped).join(Usuario).filter(
            or_(
                db.func.lower(Usuario.nombre).like(f"%{q}%"),
                db.func.lower(Usuario.apellido).like(f"%{q}%"),
                db.func.lower(Usuario.email).like(f"%{q}%"),
                db.func.lower(Huesped.documento_id).like(f"%{q}%"),
            )
        ).order_by(Huesped.created_at.desc())
    ).scalars().all()

    return [h.to_dict() for h in resultados]


def crear(id_usuario: int, documento_id: str, tipo_documento: str = "CC", preferencias: str = None):
    """Crea un huésped vinculado a un usuario existente (walk-in)."""
    usuario = db.session.get(Usuario, id_usuario)
    if not usuario:
        raise LookupError(f"Usuario con id {id_usuario} no encontrado.")

    existente = db.session.execute(
        select(Huesped).filter_by(id_usuario=id_usuario)
    ).scalar_one_or_none()
    if existente:
        raise ValueError(f"El usuario {id_usuario} ya tiene perfil de huésped.")

    if not documento_id or not documento_id.strip():
        raise ValueError("El documento_id es obligatorio.")

    huesped = Huesped(
        id_usuario=id_usuario,
        documento_id=documento_id.strip(),
        tipo_documento=tipo_documento.strip().upper() if tipo_documento else "CC",
        preferencias=preferencias.strip() if preferencias else None,
    )
    db.session.add(huesped)
    db.session.commit()
    return huesped.to_dict()


def eliminar(huesped_id: int):
    """Soft-delete: marca el huésped como inactivo."""
    huesped = db.session.get(Huesped, huesped_id)
    if not huesped:
        raise LookupError(f"Huésped con id {huesped_id} no encontrado.")

    huesped.activo = False
    db.session.commit()
    return {"mensaje": f"Huésped {huesped_id} desactivado correctamente.", "id": huesped_id}
