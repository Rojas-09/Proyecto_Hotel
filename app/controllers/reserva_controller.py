from flask import Blueprint, jsonify, request

from app.schemas.reserva_schema import CrearReservaSchema
import app.services.reserva_service as reserva_service
from app.utils.error_helper import handle_service_error
from app.utils.jwt_helper import token_required, rol_requerido

reserva_bp = Blueprint("reservas", __name__, url_prefix="/api/v1/reservas")


@reserva_bp.route("/", methods=["POST"])
@token_required
@rol_requerido("cliente", "recepcionista", "admin")
def crear(current_user):
    datos = request.get_json() or {}
    errors = CrearReservaSchema().validate(datos)
    if errors:
        return jsonify({
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": errors}
        }), 422

    try:
        reserva = reserva_service.crear(datos, current_user)
        return jsonify({
            "success": True,
            "data": reserva,
            "mensaje": "Reserva creada correctamente."
        }), 201
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)
    except PermissionError as e:
        return handle_service_error(e, 403)
    except Exception as e:
        return handle_service_error(e, 500)


@reserva_bp.route("/", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista", "gerente")
def obtener_todas(current_user):
    filtros = {
        "estado": request.args.get("estado"),
        "id_huesped": request.args.get("id_huesped"),
        "fecha_entrada": request.args.get("fecha_entrada"),
    }
    filtros = {k: v for k, v in filtros.items() if v is not None}

    try:
        reservas = reserva_service.obtener_todas(filtros or None)
        return jsonify({
            "success": True,
            "data": reservas,
            "total": len(reservas),
            "mensaje": "Reservas obtenidas correctamente."
        }), 200
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)


@reserva_bp.route("/mis-reservas", methods=["GET"])
@token_required
@rol_requerido("cliente")
def obtener_mis_reservas(current_user):
    try:
        reservas = reserva_service.obtener_mis_reservas(current_user)
        return jsonify({
            "success": True,
            "data": reservas,
            "total": len(reservas),
            "mensaje": "Tus reservas obtenidas correctamente."
        }), 200
    except Exception as e:
        return handle_service_error(e, 500)


@reserva_bp.route("/<int:reserva_id>", methods=["GET"])
@token_required
def obtener_por_id(current_user, reserva_id):
    try:
        reserva = reserva_service.obtener_por_id(reserva_id, current_user)
        return jsonify({
            "success": True,
            "data": reserva,
            "mensaje": "Reserva encontrada."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except PermissionError as e:
        return handle_service_error(e, 403)
    except Exception as e:
        return handle_service_error(e, 500)


@reserva_bp.route("/<int:reserva_id>/confirmar", methods=["PUT"])
@token_required
@rol_requerido("admin")
def confirmar(current_user, reserva_id):
    try:
        reserva = reserva_service.confirmar(reserva_id)
        return jsonify({
            "success": True,
            "data": reserva,
            "mensaje": "Reserva confirmada correctamente."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)


@reserva_bp.route("/<int:reserva_id>/cancelar", methods=["PUT"])
@token_required
def cancelar(current_user, reserva_id):
    datos = request.get_json() or {}
    motivo = datos.get("motivo")

    try:
        reserva = reserva_service.cancelar(reserva_id, motivo, current_user)
        return jsonify({
            "success": True,
            "data": reserva,
            "mensaje": "Reserva cancelada correctamente."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)
    except PermissionError as e:
        return handle_service_error(e, 403)
    except Exception as e:
        return handle_service_error(e, 500)


@reserva_bp.route("/<int:reserva_id>/checkin", methods=["PUT"])
@token_required
@rol_requerido("admin", "recepcionista")
def hacer_checkin(current_user, reserva_id):
    try:
        reserva = reserva_service.hacer_checkin(reserva_id, realizado_por_id=current_user.id)
        return jsonify({
            "success": True,
            "data": reserva,
            "mensaje": "Check-in realizado correctamente."
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)


@reserva_bp.route("/<int:reserva_id>/checkout", methods=["PUT"])
@token_required
@rol_requerido("admin", "recepcionista")
def hacer_checkout(current_user, reserva_id):
    try:
        reserva = reserva_service.hacer_checkout(reserva_id, realizado_por_id=current_user.id)
        return jsonify({
            "success": True,
            "data": reserva,
            "mensaje": (
                "Check-out realizado correctamente. "
                f"Puntos ganados: {reserva.get('puntos_ganados', 0)}"
            )
        }), 200
    except LookupError as e:
        return handle_service_error(e, 404)
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)
