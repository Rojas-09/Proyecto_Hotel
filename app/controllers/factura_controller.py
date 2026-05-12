"""
Factura Controller - Endpoints REST para facturación (RF-06)
Gestión de facturas: consulta, emisión, descarga y anulación.
"""

import io
import os

from flask import Blueprint, jsonify, request, send_file

from app.services import factura_service
from app.utils.jwt_helper import rol_requerido, token_required

factura_bp = Blueprint("factura", __name__, url_prefix="/api/v1/facturas")


@factura_bp.route("/reserva/<int:reserva_id>", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista")
def get_factura_por_reserva(current_user, reserva_id):
    """
    GET /api/v1/facturas/reserva/<reserva_id>

    Obtiene la factura asociada a una reserva.
    Roles permitidos: admin, recepcionista.
    """
    try:
        factura = factura_service.obtener_por_reserva(reserva_id)
        return jsonify({"success": True, "data": factura, "mensaje": "Factura encontrada."}), 200
    except LookupError as e:
        return jsonify({"success": False, "data": None, "mensaje": str(e)}), 404


@factura_bp.route("/reserva/<int:reserva_id>/emitir", methods=["POST"])
@token_required
@rol_requerido("admin", "recepcionista")
def emitir_factura(current_user, reserva_id):
    """
    POST /api/v1/facturas/reserva/<reserva_id>/emitir

    Emite (genera) una factura en estado pendiente.
    Calcula totales, genera PDF y cambia estado a 'emitida'.
    Roles permitidos: admin, recepcionista.
    """
    try:
        factura = factura_service.emitir(reserva_id)
        return jsonify(
            {"success": True, "data": factura, "mensaje": "Factura emitida correctamente."}
        ), 201
    except LookupError as e:
        return jsonify({"success": False, "data": None, "mensaje": str(e)}), 404
    except ValueError as e:
        return jsonify({"success": False, "data": None, "mensaje": str(e)}), 400


@factura_bp.route("/reserva/<int:reserva_id>/descargar", methods=["GET"])
@token_required
@rol_requerido("admin", "recepcionista", "cliente")
def descargar_factura(current_user, reserva_id):
    """
    GET /api/v1/facturas/reserva/<reserva_id>/descargar

    Descarga el PDF de una factura.
    Admin/recepcionista: cualquier reserva.
    Cliente: solo su propia reserva.
    """
    try:
        from app.models.reserva import Reserva
        from app.models.huesped import Huesped

        rol_value = (
            current_user.rol.value
            if hasattr(current_user.rol, "value")
            else current_user.rol
        )
        if rol_value == "cliente":
            huesped = Huesped.query.filter_by(id_usuario=current_user.id).first()
            reserva = Reserva.query.get(reserva_id)
            if not huesped or not reserva or reserva.id_huesped != huesped.id:
                return jsonify(
                    {
                        "success": False,
                        "data": None,
                        "mensaje": "No tiene permiso para descargar esta factura.",
                    }
                ), 403

        pdf_path = factura_service.descargar(reserva_id)
        with open(pdf_path, "rb") as f:
            pdf_bytes = io.BytesIO(f.read())

        os.remove(pdf_path)

        return send_file(
            pdf_bytes,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="factura.pdf",
        )
    except LookupError as e:
        return jsonify({"success": False, "data": None, "mensaje": str(e)}), 404
    except FileNotFoundError as e:
        return jsonify({"success": False, "data": None, "mensaje": str(e)}), 404
    except ValueError as e:
        return jsonify({"success": False, "data": None, "mensaje": str(e)}), 400


@factura_bp.route("/<int:factura_id>/anular", methods=["PUT"])
@token_required
@rol_requerido("admin")
def anular_factura(current_user, factura_id):
    """
    PUT /api/v1/facturas/<factura_id>/anular

    Anula una factura emitida (no pagada).
    Roles permitidos: admin.
    """
    datos = request.get_json() or {}
    motivo = datos.get("motivo", "Sin motivo especificado")

    try:
        resultado = factura_service.anular(factura_id, motivo)
        return jsonify(
            {"success": True, "data": resultado, "mensaje": "Factura anulada correctamente."}
        ), 200
    except LookupError as e:
        return jsonify({"success": False, "data": None, "mensaje": str(e)}), 404
    except ValueError as e:
        return jsonify({"success": False, "data": None, "mensaje": str(e)}), 400