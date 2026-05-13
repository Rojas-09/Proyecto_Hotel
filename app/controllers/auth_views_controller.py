from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from app.services.auth_service import AuthService
from app.models.usuario import RolEnum

auth_views_bp = Blueprint('auth_views', __name__)

@auth_views_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        flash('Email y contraseña son requeridos.', 'danger')
        return redirect(url_for('views.login'))
    
    # Usamos el AuthService para validar las credenciales
    # Nota: AuthService.login espera un dict y devuelve (result, status)
    result, status = AuthService.login({'email': email, 'password': password})
    
    if status == 200:
        user_data = result['data']['usuario']
        # Guardamos en la sesión de Flask para las vistas HTML
        session['user_id'] = user_data['id']
        session['user_email'] = user_data['email']
        session['user_rol'] = user_data['rol']
        session['user_nombre'] = f"{user_data['nombre']} {user_data['apellido']}"
        
        flash(f'Bienvenido, {user_data["nombre"]}.', 'success')
        
        # Redirección según rol
        rol = user_data['rol']
        if rol == RolEnum.admin.value:
            return redirect(url_for('views.admin_dashboard'))
        elif rol == RolEnum.recepcionista.value:
            return redirect(url_for('views.recepcionista_dashboard'))
        else:
            return redirect(url_for('views.cliente_dashboard'))
    else:
        error_msg = result.get('error', {}).get('message', 'Credenciales inválidas.')
        flash(error_msg, 'danger')
        return redirect(url_for('views.login'))

@auth_views_bp.route('/register', methods=['POST'])
def register():
    # Lógica simplificada para registro desde la web
    data = {
        'nombre': request.form.get('nombre'),
        'apellido': request.form.get('apellido', ''), # El form de login solo tiene 'nombre'
        'email': request.form.get('email'),
        'password': request.form.get('password'),
        'telefono': request.form.get('telefono', ''),
        'documento_id': request.form.get('documento_id', '00000000'),
    }
    
    result, status = AuthService.registrar(data)
    
    if status == 201:
        flash('Registro exitoso. Por favor inicie sesión.', 'success')
        return redirect(url_for('views.login'))
    else:
        error_msg = result.get('error', {}).get('message', 'Error en el registro.')
        flash(error_msg, 'danger')
        return redirect(url_for('views.login'))
