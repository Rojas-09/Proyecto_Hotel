"""
HotelBook Pro - Application Factory
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


def create_app(config_name="development"):
    """Crea y configura la instancia de Flask (Application Factory Pattern)."""
    app = Flask(__name__)

    # Cargar configuración según entorno
    from config import config
    app.config.from_object(config[config_name])

    # Inicializar extensiones
    db.init_app(app)
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        automatic_options=True,
    )

    # Registrar Blueprints (controladores)
    from app.controllers.auth_controller import auth_bp
    from app.controllers.habitacion_controller import habitacion_bp
    from app.controllers.huesped_controller import huesped_bp
    from app.controllers.reserva_controller import reserva_bp
    from app.controllers.factura_controller import factura_bp
    from app.controllers.pago_controller import pago_bp
    from app.controllers.servicio_adicional_controller import servicio_adicional_bp
    from app.controllers.reporte_controller import reporte_bp
    from app.controllers.puntos_fidelidad_controller import puntos_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(habitacion_bp, url_prefix="/api/v1/habitaciones")
    app.register_blueprint(huesped_bp, url_prefix="/api/v1/huespedes")
    app.register_blueprint(reserva_bp, url_prefix="/api/v1/reservas")
    app.register_blueprint(factura_bp, url_prefix="/api/v1/facturas")
    app.register_blueprint(pago_bp, url_prefix="/api/v1/pagos")
    app.register_blueprint(servicio_adicional_bp)
    app.register_blueprint(reporte_bp, url_prefix="/api/v1/reportes")
    app.register_blueprint(puntos_bp, url_prefix="/api/v1/huespedes")

    # Importar modelos EN ORDEN para respetar dependencias FK
    from app.models import usuario  # noqa: F401
    from app.models import huesped  # noqa: F401
    from app.models import habitacion  # noqa: F401
    from app.models import reserva  # noqa: F401
    from app.models import checkin_checkout  # noqa: F401
    from app.models import pago  # noqa: F401
    from app.models import reembolso  # noqa: F401
    from app.models import factura  # noqa: F401
    from app.models import servicio_adicional  # noqa: F401
    from app.models import notificacion  # noqa: F401
    from app.models import puntos_fidelidad  # noqa: F401

    # Crear tablas si no existen (solo en desarrollo)
    if config_name in ("development", "testing"):
        with app.app_context():
            db.create_all()

    return app
