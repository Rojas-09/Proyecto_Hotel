"""
Notificacion Controller - Endpoints REST para notificaciones
GET    /              → listar todas (admin, recepcionista)
GET    /<id>          → obtener una (admin, recepcionista)
GET    /reserva/<reserva_id> → listar por reserva (admin, recepcionista)
POST   /              → crear (admin, recepcionista)
PUT    /<id>          → actualizar (admin, recepcionista)
DELETE /<id>          → eliminar (admin)
"""

from flask import Blueprint, jsonify, request

from app import db
from app.services import notificacion_service
from app.utils.error_helper import handle_service_error
from app.utils.jwt_helper import token_required, rol_requerido

notificacion_bp = Blueprint("notificaciones", __name__)


@notificacion_bp.route("", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def listar_notificaciones(current_user):
    filtros = {
        "tipo": request.args.get("tipo"),
        "enviado": request.args.get("enviado"),
        "fecha_desde": request.args.get("fecha_desde"),
        "fecha_hasta": request.args.get("fecha_hasta"),
    }
    # Convertir enviado a boolean si se proporciona
    if filtros.get("enviado") is not None:
        filtros["enviado"] = filtros["enviado"].lower() in ("true", "1", "yes")
    filtros = {k: v for k, v in filtros.items() if v is not None}

    try:
        notificaciones = notificacion_service.listar(filtros or None)
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "notificaciones": notificaciones,
                        "total": len(notificaciones),
                    },
                    "mensaje": "Notificaciones obtenidas correctamente.",
                }
            ),
            200,
        )
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)


@notificacion_bp.route("/buscar", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def buscar_notificaciones(current_user):
    q = request.args.get("q", "").strip()
    if not q:
        return (
            jsonify(
                {"success": False, "data": None, "mensaje": "Parámetro 'q' requerido."}
            ),
            400,
        )

    try:
        notificaciones = notificacion_service.buscar(q)
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "notificaciones": notificaciones,
                        "total": len(notificaciones),
                    },
                    "mensaje": "Búsqueda realizada correctamente.",
                }
            ),
            200,
        )
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)


@notificacion_bp.route("/<int:id>", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def obtener_notificacion(current_user, id):
    try:
        notificacion = notificacion_service.obtener(id)
        return (
            jsonify(
                {
                    "success": True,
                    "data": notificacion,
                    "mensaje": "Notificación obtenida correctamente.",
                }
            ),
            200,
        )
    except LookupError as e:
        return handle_service_error(e, 404)


@notificacion_bp.route("/reserva/<int:reserva_id>", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def listar_por_reserva(current_user, reserva_id):
    try:
        notificaciones = notificacion_service.listar_por_reserva(reserva_id)
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "notificaciones": notificaciones,
                        "total": len(notificaciones),
                    },
                    "mensaje": "Notificaciones obtenidas correctamente.",
                }
            ),
            200,
        )
    except LookupError as e:
        return handle_service_error(e, 404)


@notificacion_bp.route("", methods=["POST"])
@token_required
@rol_requerido("admin", "recepcionista")
def crear_notificacion(current_user):
    data = request.get_json(silent=True) or {}
    id_reserva = data.get("id_reserva")
    tipo = data.get("tipo")
    mensaje = data.get("mensaje")

    if not all([id_reserva, tipo, mensaje]):
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "mensaje": "Los campos 'id_reserva', 'tipo' y 'mensaje' son obligatorios.",
                }
            ),
            400,
        )

    try:
        notificacion = notificacion_service.crear(
            id_reserva=int(id_reserva), tipo=tipo, mensaje=mensaje
        )
        return (
            jsonify(
                {
                    "success": True,
                    "data": notificacion,
                    "mensaje": "Notificación creada exitosamente.",
                }
            ),
            201,
        )
    except (LookupError, ValueError) as e:
        return handle_service_error(e, 400)


@notificacion_bp.route("/<int:id>", methods=["PUT"])
@token_required
@rol_requerido("admin", "recepcionista")
def actualizar_notificacion(current_user, id):
    data = request.get_json(silent=True) or {}

    campos_validos = {"mensaje", "tipo", "enviado"}
    if not campos_validos.intersection(data.keys()):
        return (
            jsonify(
                {
                    "success": False,
                    "data": None,
                    "mensaje": "Debe enviar al menos un campo válido: mensaje, tipo, enviado.",
                }
            ),
            400,
        )

    try:
        notificacion = notificacion_service.actualizar(id, **data)
        return (
            jsonify(
                {
                    "success": True,
                    "data": notificacion,
                    "mensaje": "Notificación actualizada correctamente.",
                }
            ),
            200,
        )
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)


@notificacion_bp.route("/<int:id>", methods=["DELETE"])
@token_required
@rol_requerido("admin")
def eliminar_notificacion(current_user, id):
    try:
        notificacion_service.eliminar(id)
        db.session.commit()
        return (
            jsonify(
                {
                    "success": True,
                    "data": None,
                    "mensaje": "Notificación eliminada correctamente.",
                }
            ),
            200,
        )
    except LookupError as e:
        return handle_service_error(e, 404)
