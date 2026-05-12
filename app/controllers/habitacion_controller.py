from flask import Blueprint, jsonify, request

import app.services.habitacion_service as habitacion_service
from app.utils.jwt_helper import rol_requerido, token_required

habitacion_bp = Blueprint(
    "habitaciones", __name__, url_prefix="/api/v1/habitaciones"
)


@habitacion_bp.route("/", methods=["GET"])
def listar():
    filtros = {
        "tipo": request.args.get("tipo"),
        "estado": request.args.get("estado"),
        "piso": request.args.get("piso"),
    }
    filtros = {k: v for k, v in filtros.items() if v is not None}

    try:
        habitaciones = habitacion_service.obtener_todas(filtros or None)
        return jsonify({
            "success": True,
            "data": habitaciones,
            "total": len(habitaciones),
            "mensaje": "Habitaciones obtenidas correctamente."
        }), 200
    except ValueError as e:
        return jsonify({"success": False, "mensaje": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "mensaje": "Error interno del servidor.",
            "detalle": str(e)
        }), 500


@habitacion_bp.route("/disponibles", methods=["GET"])
def disponibles():
    fecha_entrada = request.args.get("fecha_entrada")
    fecha_salida = request.args.get("fecha_salida")
    tipo = request.args.get("tipo")

    if not fecha_entrada or not fecha_salida:
        return jsonify({
            "success": False,
            "mensaje": "Se requieren los parametros fecha_entrada y fecha_salida (YYYY-MM-DD)."
        }), 400

    try:
        habitaciones = habitacion_service.buscar_disponibles(
            fecha_entrada, fecha_salida, tipo
        )
        return jsonify({
            "success": True,
            "data": habitaciones,
            "total": len(habitaciones),
            "mensaje": f"{len(habitaciones)} habitacion(es) disponible(s) encontrada(s)."
        }), 200
    except ValueError as e:
        return jsonify({"success": False, "mensaje": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "mensaje": "Error interno del servidor.",
            "detalle": str(e)
        }), 500


@habitacion_bp.route("/<int:habitacion_id>", methods=["GET"])
def obtener(habitacion_id):
    try:
        habitacion = habitacion_service.obtener_por_id(habitacion_id)
        return jsonify({
            "success": True,
            "data": habitacion,
            "mensaje": "Habitacion encontrada."
        }), 200
    except LookupError as e:
        return jsonify({"success": False, "mensaje": str(e)}), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "mensaje": "Error interno del servidor.",
            "detalle": str(e)
        }), 500


@habitacion_bp.route("/", methods=["POST"])
@token_required
@rol_requerido("admin")
def crear(current_user):
    datos = request.get_json()
    if not datos:
        return jsonify({
            "success": False,
            "mensaje": "El cuerpo de la solicitud debe ser JSON."
        }), 400

    try:
        habitacion = habitacion_service.crear(datos)
        return jsonify({
            "success": True,
            "data": habitacion,
            "mensaje": f"Habitacion {habitacion['numero']} creada correctamente."
        }), 201
    except ValueError as e:
        return jsonify({"success": False, "mensaje": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "mensaje": "Error interno del servidor.",
            "detalle": str(e)
        }), 500


@habitacion_bp.route("/<int:habitacion_id>", methods=["PUT"])
@token_required
@rol_requerido("admin")
def actualizar(current_user, habitacion_id):
    datos = request.get_json()
    if not datos:
        return jsonify({
            "success": False,
            "mensaje": "El cuerpo de la solicitud debe ser JSON."
        }), 400

    try:
        habitacion = habitacion_service.actualizar(habitacion_id, datos)
        return jsonify({
            "success": True,
            "data": habitacion,
            "mensaje": f"Habitacion {habitacion['numero']} actualizada correctamente."
        }), 200
    except LookupError as e:
        return jsonify({"success": False, "mensaje": str(e)}), 404
    except ValueError as e:
        return jsonify({"success": False, "mensaje": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "mensaje": "Error interno del servidor.",
            "detalle": str(e)
        }), 500


@habitacion_bp.route("/<int:habitacion_id>", methods=["DELETE"])
@token_required
@rol_requerido("admin")
def eliminar(current_user, habitacion_id):
    try:
        resultado = habitacion_service.eliminar(habitacion_id)
        return jsonify({
            "success": True,
            "data": None,
            "mensaje": resultado["mensaje"]
        }), 200
    except LookupError as e:
        return jsonify({"success": False, "mensaje": str(e)}), 404
    except ValueError as e:
        return jsonify({"success": False, "mensaje": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "mensaje": "Error interno del servidor.",
            "detalle": str(e)
        }), 500
