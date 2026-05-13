from flask import Blueprint, render_template, request

from sqlalchemy import select

from app import db
from app.models.habitacion import Habitacion, EstadoHabitacion, TipoHabitacion

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def home():
    """Renderiza la página de inicio con habitaciones destacadas."""
    result = db.session.execute(
        select(Habitacion)
        .filter_by(estado=EstadoHabitacion.disponible)
        .order_by(Habitacion.precio_noche.desc())
        .limit(3)
    )
    destacadas = result.scalars().all()
    return render_template('public/home.html', habitaciones=destacadas)


@views_bp.route('/login')
def login():
    return render_template('public/login.html')


@views_bp.route('/habitaciones')
def habitaciones():
    """Renderiza la lista de habitaciones con filtros."""
    tipo_query = request.args.get('tipo', '').lower()
    query = select(Habitacion)
    
    if tipo_query:
        for tipo_enum in TipoHabitacion:
            if tipo_enum.value == tipo_query:
                query = query.filter(Habitacion.tipo == tipo_enum)
                break
    
    result = db.session.execute(query)
    habitaciones_list = result.scalars().all()
    return render_template('public/habitaciones.html', habitaciones=habitaciones_list)


@views_bp.route('/habitaciones/<int:id>')
def detalle_habitacion(id):
    """Renderiza el detalle de una habitación."""
    habitacion = db.session.get(Habitacion, id)
    if not habitacion:
        return render_template('public/habitaciones.html', habitaciones=[])
    return render_template('public/detalle_habitacion.html', habitacion=habitacion)


@views_bp.route('/reservar')
def reserva():
    """Renderiza la página de checkout."""
    habitacion_id = request.args.get('habitacion_id')
    habitacion = None
    if habitacion_id:
        habitacion = db.session.get(Habitacion, habitacion_id)
    return render_template('cliente/reserva.html', habitacion=habitacion)


@views_bp.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')


@views_bp.route('/recepcionista/dashboard')
def recepcionista_dashboard():
    return render_template('recepcionista/dashboard.html')


@views_bp.route('/mis-reservas')
def mis_reservas():
    return render_template('cliente/mis_reservas.html')


@views_bp.route('/endpoints')
def endpoints():
    """Renderiza la página de documentación de endpoints."""
    ui_pages = [
        {'name': 'Inicio', 'path': '/', 'method': 'GET', 'description': 'Página de hero con habitaciones destacadas'},
        {'name': 'Login', 'path': '/login', 'method': 'GET', 'description': 'Auth页面 para usuario'},
        {'name': 'Habitaciones', 'path': '/habitaciones', 'method': 'GET', 'description': 'Listado completo con filtros'},
        {'name': 'Detalle Habitación', 'path': '/habitaciones/<id>', 'method': 'GET', 'description': 'Ficha técnica individual'},
        {'name': 'Checkout', 'path': '/reservar', 'method': 'GET', 'description': 'Confirmación de reserva'},
        {'name': 'Endpoints', 'path': '/endpoints', 'method': 'GET', 'description': 'Documentación visual de API'},
    ]
    
    api_groups = [
        {'title': 'Autenticación', 'prefix': '/api/v1/auth', 'items': [
            {'method': 'POST', 'path': '/register', 'description': 'Registro de usuario nuevo'},
            {'method': 'POST', 'path': '/login', 'description': 'Inicio de sesión JWT'},
            {'method': 'GET', 'path': '/me', 'description': 'Datos del usuario autenticado'},
            {'method': 'GET', 'path': '/usuarios', 'description': 'Listado de usuarios (admin)'},
            {'method': 'GET', 'path': '/usuarios/<id>', 'description': 'Obtener usuario específico'},
        ]},
        {'title': 'Habitaciones', 'prefix': '/api/v1/habitaciones', 'items': [
            {'method': 'GET', 'path': '/', 'description': 'Listar habitaciones disponibles'},
            {'method': 'GET', 'path': '/<id>', 'description': 'Obtener detalle de habitación'},
            {'method': 'GET', 'path': '/disponibilidad', 'description': 'Consultar disponibilidad por fechas'},
        ]},
        {'title': 'Reservas', 'prefix': '/api/v1/reservas', 'items': [
            {'method': 'GET', 'path': '/', 'description': 'Listar reservas (filtradas por usuario)'},
            {'method': 'POST', 'path': '/', 'description': 'Crear nueva reserva'},
            {'method': 'PUT', 'path': '/<id>', 'description': 'Actualizar reserva'},
            {'method': 'DELETE', 'path': '/<id>', 'description': 'Eliminar reserva'},
            {'method': 'GET', 'path': '/mis-reservas', 'description': 'Reservas del usuario autenticado'},
        ]},
        {'title': 'Pagos', 'prefix': '/api/v1/pagos', 'items': [
            {'method': 'POST', 'path': '/procesar', 'description': 'Procesar pago con Stripe'},
            {'method': 'POST', 'path': '/confirmar', 'description': 'Confirmar pago exitoso'},
            {'method': 'GET', 'path': '/<id>', 'description': 'Obtener detalle de pago'},
        ]},
        {'title': 'Reportes', 'prefix': '/api/v1/reportes', 'items': [
            {'method': 'GET', 'path': '/ocupacion', 'description': 'Reporte de ocupación por fechas'},
            {'method': 'GET', 'path': '/ingresos', 'description': 'Reporte de ingresos'},
        ]},
    ]
    
    return render_template('public/endpoints.html', ui_pages=ui_pages, api_groups=api_groups)
