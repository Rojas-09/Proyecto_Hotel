"""
Reporte Controller - Endpoints REST para reportes (RF-08)
Genera y descarga reportes en formato xlsx y pdf.
"""

import os
from datetime import date
from flask import Blueprint, jsonify, request, send_file

from app.services import reporte_service
from app.utils.error_helper import handle_service_error
from app.utils.jwt_helper import rol_requerido, token_required

reporte_bp = Blueprint("reporte", __name__, url_prefix="/api/v1/reportes")


def _validar_fechas(fecha_inicio: str, fecha_fin: str):
    """Valida que las fechas estén presentes y en formato correcto."""
    if not fecha_inicio or not fecha_fin:
        raise ValueError("Los parámetros 'fecha_inicio' y 'fecha_fin' son obligatorios.")
    try:
        date.fromisoformat(fecha_inicio)
    except (ValueError, TypeError):
        raise ValueError(
            "El formato de 'fecha_inicio' es inválido. Use: YYYY-MM-DD."
        )
    try:
        date.fromisoformat(fecha_fin)
    except (ValueError, TypeError):
        raise ValueError(
            "El formato de 'fecha_fin' es inválido. Use: YYYY-MM-DD."
        )


@reporte_bp.route("/ocupacion", methods=["GET"])
@token_required
@rol_requerido("admin", "gerente")
def reporte_ocupacion(current_user):
    """
    GET /api/v1/reportes/ocupacion?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD&formato=xlsx

    Genera reporte de ocupación de habitaciones.
    Formatos: xlsx (default), pdf.
    Roles permitidos: admin, gerente.
    """
    fecha_inicio = request.args.get("fecha_inicio", "")
    fecha_fin = request.args.get("fecha_fin", "")
    formato = request.args.get("formato", "xlsx").lower()

    if formato not in ("xlsx", "pdf"):
        return jsonify({
            "success": False,
            "data": None,
            "mensaje": "Formato no soportado. Use 'xlsx' o 'pdf'.",
        }), 400

    try:
        _validar_fechas(fecha_inicio, fecha_fin)
    except ValueError as e:
        return handle_service_error(e, 400)

    try:
        resultado = reporte_service.generar_ocupacion(
            fecha_inicio, fecha_fin, formato, creado_por=current_user.id
        )
        archivo = resultado["archivo"]
        if not os.path.exists(archivo):
            return jsonify({
                "success": False,
                "data": None,
                "mensaje": "Error al generar el archivo del reporte.",
            }), 500

        mime = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if formato == "xlsx" else "application/pdf"
        )
        nombre_descarga = f"reporte_ocupacion_{fecha_inicio}_{fecha_fin}.{formato}"
        return send_file(
            archivo,
            mimetype=mime,
            as_attachment=True,
            download_name=nombre_descarga,
        )
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)


@reporte_bp.route("/ingresos", methods=["GET"])
@token_required
@rol_requerido("admin", "gerente")
def reporte_ingresos(current_user):
    """
    GET /api/v1/reportes/ingresos?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD&formato=xlsx

    Genera reporte de ingresos por período.
    Formatos: xlsx (default), pdf.
    Roles permitidos: admin, gerente.
    """
    fecha_inicio = request.args.get("fecha_inicio", "")
    fecha_fin = request.args.get("fecha_fin", "")
    formato = request.args.get("formato", "xlsx").lower()

    if formato not in ("xlsx", "pdf"):
        return jsonify({
            "success": False,
            "data": None,
            "mensaje": "Formato no soportado. Use 'xlsx' o 'pdf'.",
        }), 400

    try:
        _validar_fechas(fecha_inicio, fecha_fin)
    except ValueError as e:
        return handle_service_error(e, 400)

    try:
        resultado = reporte_service.generar_ingresos(
            fecha_inicio, fecha_fin, formato, creado_por=current_user.id
        )
        archivo = resultado["archivo"]
        if not os.path.exists(archivo):
            return jsonify({
                "success": False,
                "data": None,
                "mensaje": "Error al generar el archivo del reporte.",
            }), 500

        mime = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if formato == "xlsx" else "application/pdf"
        )
        nombre_descarga = f"reporte_ingresos_{fecha_inicio}_{fecha_fin}.{formato}"
        return send_file(
            archivo,
            mimetype=mime,
            as_attachment=True,
            download_name=nombre_descarga,
        )
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)


@reporte_bp.route("/estadisticas", methods=["GET"])
@token_required
@rol_requerido("admin", "gerente")
def reporte_estadisticas(current_user):
    """
    GET /api/v1/reportes/estadisticas?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD&formato=xlsx

    Genera reporte de estadísticas generales.
    Formatos: xlsx (default), pdf.
    Roles permitidos: admin, gerente.
    """
    fecha_inicio = request.args.get("fecha_inicio", "")
    fecha_fin = request.args.get("fecha_fin", "")
    formato = request.args.get("formato", "xlsx").lower()

    if formato not in ("xlsx", "pdf"):
        return jsonify({
            "success": False,
            "data": None,
            "mensaje": "Formato no soportado. Use 'xlsx' o 'pdf'.",
        }), 400

    try:
        _validar_fechas(fecha_inicio, fecha_fin)
    except ValueError as e:
        return handle_service_error(e, 400)

    try:
        resultado = reporte_service.generar_estadisticas(
            fecha_inicio, fecha_fin, formato, creado_por=current_user.id
        )
        archivo = resultado["archivo"]
        if not os.path.exists(archivo):
            return jsonify({
                "success": False,
                "data": None,
                "mensaje": "Error al generar el archivo del reporte.",
            }), 500

        mime = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if formato == "xlsx" else "application/pdf"
        )
        nombre_descarga = f"reporte_estadisticas_{fecha_inicio}_{fecha_fin}.{formato}"
        return send_file(
            archivo,
            mimetype=mime,
            as_attachment=True,
            download_name=nombre_descarga,
        )
    except ValueError as e:
        return handle_service_error(e, 400)
    except Exception as e:
        return handle_service_error(e, 500)
