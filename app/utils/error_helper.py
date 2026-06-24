from flask import current_app, jsonify, request

_DOMAIN_EXCEPTIONS = (LookupError, ValueError, PermissionError)


def handle_service_error(e, status_code=400):
    current_app.logger.error(
        "Error en %s [%s]: %s", request.path, type(e).__name__, str(e), exc_info=True
    )
    if isinstance(e, _DOMAIN_EXCEPTIONS):
        return jsonify({"success": False, "data": None, "mensaje": str(e)}), status_code
    mensaje = str(e) if current_app.debug else "Error interno del servidor."
    return jsonify({"success": False, "data": None, "mensaje": mensaje}), status_code
