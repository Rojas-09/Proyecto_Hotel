from functools import wraps

from flask import flash, redirect, session, url_for


def _revalidar_usuario():
    """Retorna False si el usuario fue desactivado o eliminado."""
    user_id = session.get("user_id")
    if not user_id:
        return False
    from app import db
    from app.models.usuario import Usuario
    user = db.session.get(Usuario, user_id)
    if not user or not user.activo:
        session.clear()
        return False
    return True


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor inicie sesión para acceder.", "warning")
            return redirect(url_for("views.login"))
        if not _revalidar_usuario():
            flash("Su cuenta ha sido desactivada.", "warning")
            return redirect(url_for("views.login"))
        return f(*args, **kwargs)
    return decorated_function


def roles_allowed(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Por favor inicie sesión para acceder.", "warning")
                return redirect(url_for("views.login"))
            if not _revalidar_usuario():
                flash("Su cuenta ha sido desactivada.", "warning")
                return redirect(url_for("views.login"))
            rol = session.get("user_rol")
            valores = [r.value if hasattr(r, "value") else r for r in roles]
            if rol not in valores:
                flash(
                    "No tiene permisos para acceder a esta sección.",
                    "danger",
                )
                return redirect(url_for("views.home"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
