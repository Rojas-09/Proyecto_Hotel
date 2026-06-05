from functools import wraps

from flask import (
    Blueprint, flash, redirect, render_template,
    request, session, url_for,
)
from sqlalchemy import select

from app import db
from app.models.habitacion import (
    EstadoHabitacion, Habitacion, TipoHabitacion,
)
from app.models.usuario import Usuario
from app.services.auth_service import AuthService

views_bp = Blueprint("views", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("views.login_page", next=request.url))
        return f(*args, **kwargs)
    return decorated


def rol_requerido(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            rol = session.get("user_rol")
            valores = [r.value if hasattr(r, "value") else r for r in roles]
            if rol not in valores:
                flash(
                    "No tienes permisos para acceder a esta sección.",
                    "danger",
                )
                return redirect(url_for("views.home"))
            return f(*args, **kwargs)
        return decorated
    return decorator


@views_bp.route("/api-test")
@login_required
@rol_requerido("admin")
def api_test():
    return render_template("public/api_test.html")


@views_bp.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("views._dashboard_por_rol"))
    return render_template("public/login.html")


@views_bp.route("/login", methods=["POST"])
def login_submit():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Email y contraseña son obligatorios.", "danger")
        return render_template("public/login.html", email=email)

    result, status = AuthService.login({"email": email, "password": password})

    if status != 200:
        msg = result.get("error", {}).get("message", "Credenciales inválidas.")
        flash(msg, "danger")
        return render_template("public/login.html", email=email)

    token = result.get("data", {}).get("token")
    if not token:
        flash("Error interno. Intenta nuevamente.", "danger")
        return render_template("public/login.html", email=email)

    from app.utils.jwt_helper import decodificar_token
    try:
        payload = decodificar_token(token)
    except Exception:
        flash("Token inválido. Intenta nuevamente.", "danger")
        return render_template("public/login.html", email=email)

    user = db.session.get(Usuario, payload["user_id"])
    if not user or not user.activo:
        flash("Usuario no encontrado o inactivo.", "danger")
        return render_template("public/login.html", email=email)

    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_rol"] = user.rol.value
    session["user_nombre"] = user.nombre
    session["jwt_token"] = token
    session.permanent = True

    flash(f"Bienvenido, {user.nombre}.", "success")

    next_url = request.args.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(url_for("views._dashboard_por_rol"))


@views_bp.route("/registro")
def register_page():
    if "user_id" in session:
        return redirect(url_for("views._dashboard_por_rol"))
    return render_template("public/register.html")


@views_bp.route("/registro", methods=["POST"])
def register_submit():
    data = request.form
    required = [
        "nombre", "apellido", "email", "password",
        "telefono", "documento_id",
    ]
    for field in required:
        if not data.get(field, "").strip():
            flash(f"El campo {field} es obligatorio.", "danger")
            return render_template("public/register.html", form_data=data)

    if data.get("password") != data.get("password_confirm"):
        flash("Las contraseñas no coinciden.", "danger")
        return render_template("public/register.html", form_data=data)

    payload = {
        "nombre": data["nombre"].strip(),
        "apellido": data["apellido"].strip(),
        "email": data["email"].strip(),
        "password": data["password"],
        "telefono": data.get("telefono", "").strip(),
        "documento_id": data["documento_id"].strip(),
        "tipo_documento": data.get("tipo_documento", "CC").strip(),
    }

    result, status = AuthService.registrar(payload)

    if status != 201:
        msg = result.get("error", {}).get("message", "Error en el registro.")
        flash(msg, "danger")
        return render_template("public/register.html", form_data=data)

    flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
    return redirect(url_for("views.login_page"))


@views_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("views.home"))


@views_bp.route("/_dashboard")
def _dashboard_por_rol():
    rol = session.get("user_rol")
    if rol == "cliente":
        return redirect(url_for("views.mis_reservas"))
    elif rol in ("admin", "gerente"):
        return redirect(url_for("views.admin_dashboard"))
    elif rol == "recepcionista":
        return redirect(url_for("views.recepcionista_dashboard"))
    return redirect(url_for("views.home"))


@views_bp.route("/")
def home():
    result = db.session.execute(
        select(Habitacion)
        .filter_by(estado=EstadoHabitacion.disponible)
        .order_by(Habitacion.precio_noche.desc())
        .limit(6)
    )
    habitaciones = result.scalars().all()
    return render_template("public/home.html", habitaciones=habitaciones)


@views_bp.route("/habitaciones")
def habitaciones():
    tipo_q = request.args.get("tipo", "").strip().lower()
    estado_q = request.args.get("estado", "").strip().lower()

    query = select(Habitacion).filter_by(activo=True)
    user_rol = session.get("user_rol")
    es_privilegiado = user_rol in ("admin", "gerente", "recepcionista")

    if not es_privilegiado:
        query = query.filter(Habitacion.estado == EstadoHabitacion.disponible)
    elif estado_q:
        for e in EstadoHabitacion:
            if e.value == estado_q:
                query = query.filter(Habitacion.estado == e)
                break

    if tipo_q:
        for t in TipoHabitacion:
            if t.value == tipo_q:
                query = query.filter(Habitacion.tipo == t)
                break

    result = db.session.execute(query.order_by(Habitacion.numero))
    habitaciones_list = result.scalars().all()
    return render_template(
        "public/habitaciones.html",
        habitaciones=habitaciones_list,
        filtro_tipo=tipo_q,
        filtro_estado=estado_q,
        es_privilegiado=es_privilegiado,
    )


@views_bp.route("/habitaciones/<int:hab_id>")
def detalle_habitacion(hab_id):
    habitacion = db.session.get(Habitacion, hab_id)
    if not habitacion:
        flash("Habitación no encontrada.", "warning")
        return redirect(url_for("views.habitaciones"))
    return render_template(
        "public/detalle_habitacion.html", habitacion=habitacion
    )


@views_bp.route("/reservar")
@login_required
def reserva():
    if session["user_rol"] != "cliente":
        flash("Solo clientes pueden hacer reservas.", "warning")
        return redirect(url_for("views.home"))

    hab_id = request.args.get("habitacion_id")
    habitacion = None
    if hab_id:
        habitacion = db.session.get(Habitacion, hab_id)
        if not habitacion or not habitacion.activo:
            flash("Habitación no disponible.", "warning")
            return redirect(url_for("views.habitaciones"))
    return render_template("cliente/reserva.html", habitacion=habitacion)


@views_bp.route("/mis-reservas")
@login_required
def mis_reservas():
    return render_template("cliente/mis_reservas.html")


@views_bp.route("/mis-reservas/<int:reserva_id>")
@login_required
def detalle_reserva(reserva_id):
    return render_template(
        "cliente/detalle_reserva.html", reserva_id=reserva_id
    )


@views_bp.route("/recepcionista/dashboard")
@login_required
@rol_requerido("recepcionista")
def recepcionista_dashboard():
    return render_template("recepcionista/dashboard.html")


@views_bp.route("/recepcionista/reservas")
@login_required
@rol_requerido("recepcionista")
def recepcionista_reservas():
    return render_template("recepcionista/reservas.html")


@views_bp.route("/recepcionista/checkin")
@login_required
@rol_requerido("recepcionista")
def recepcionista_checkin():
    return render_template("recepcionista/checkin_checkout.html")


@views_bp.route("/recepcionista/servicios")
@login_required
@rol_requerido("recepcionista")
def recepcionista_servicios():
    return render_template("recepcionista/servicios.html")


@views_bp.route("/recepcionista/huespedes")
@login_required
@rol_requerido("recepcionista")
def recepcionista_huespedes():
    return render_template("recepcionista/huespedes.html")


@views_bp.route("/admin/dashboard")
@login_required
@rol_requerido("admin", "gerente")
def admin_dashboard():
    return render_template("admin/dashboard.html")


@views_bp.route("/admin/usuarios")
@login_required
@rol_requerido("admin")
def usuarios():
    return render_template("admin/usuarios.html")


@views_bp.route("/admin/habitaciones")
@login_required
@rol_requerido("admin")
def gestion_habitaciones():
    return render_template("admin/gestion_habitaciones.html")


@views_bp.route("/admin/habitaciones/<int:hab_id>/editar")
@login_required
@rol_requerido("admin")
def editar_habitacion(hab_id):
    habitacion = db.session.get(Habitacion, hab_id)
    if not habitacion:
        flash("Habitación no encontrada.", "warning")
        return redirect(url_for("views.gestion_habitaciones"))
    return render_template(
        "admin/editar_habitacion.html", habitacion=habitacion
    )


@views_bp.route("/admin/reportes")
@login_required
@rol_requerido("admin", "gerente")
def reportes():
    return render_template("admin/reportes.html")
