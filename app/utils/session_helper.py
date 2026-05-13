from functools import wraps
from flask import session, redirect, url_for, flash
from app.models.usuario import RolEnum

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder.', 'warning')
            return redirect(url_for('views.login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_allowed(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_rol' not in session or session['user_rol'] not in [r.value if hasattr(r, 'value') else r for r in roles]:
                flash('No tiene permisos para acceder a esta sección.', 'danger')
                return redirect(url_for('views.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
