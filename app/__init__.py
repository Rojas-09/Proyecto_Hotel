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
    CORS(app)

    # Registrar Blueprints (controladores)
    from app.controllers.auth_controller import auth_bp
    from app.controllers.habitacion_controller import habitacion_bp
    from app.controllers.reserva_controller import reserva_bp
    from app.controllers.factura_controller import factura_bp
    from app.controllers.servicio_controller import servicio_bp
    from app.controllers.reporte_controller import reporte_bp

    app.register_blueprint(auth_bp,       url_prefix="/api/v1/auth")
    app.register_blueprint(habitacion_bp, url_prefix="/api/v1/habitaciones")
    app.register_blueprint(reserva_bp,    url_prefix="/api/v1/reservas")
    app.register_blueprint(factura_bp,    url_prefix="/api/v1/facturas")
    app.register_blueprint(servicio_bp,   url_prefix="/api/v1/servicios")
    app.register_blueprint(reporte_bp,    url_prefix="/api/v1/reportes")

    # Crear tablas si no existen (solo en desarrollo)
    with app.app_context():
        db.create_all()

    return app