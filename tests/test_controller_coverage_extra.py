"""
Tests para caminos de error en controllers con cobertura <90%.
"""
from datetime import date, timedelta

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.usuario import RolEnum, Usuario
from app.models.reserva import EstadoReserva, Reserva
from app.models.servicio_adicional import ServicioAdicional, TipoServicio


def _hdr(user):
    """Genera header de autorización. Llama ANTES de db.session.commit()."""
    from app.utils.jwt_helper import generar_token
    tok = generar_token(user.id, user.rol.value, user.email)
    return {"Authorization": f"Bearer {tok}"}


def _u(rol, tag):
    u = Usuario(nombre="U", apellido=tag,
                email=f"{tag}_{id(tag)}@h.com", rol=rol)
    u.password = "p"
    db.session.add(u)
    db.session.flush()
    return u


def _h(u):
    h = Huesped(id_usuario=u.id, documento_id=f"CC{u.id:05d}")
    db.session.add(h)
    db.session.flush()
    return h


def _hab(n="C999"):
    h = Habitacion(numero=n, tipo=TipoHabitacion.doble, precio_noche=100000,
                   capacidad=2, piso=1, estado=EstadoHabitacion.disponible)
    db.session.add(h)
    db.session.flush()
    return h


class TestAuthController:
    """Cubre auth_controller.py: 30, 77, 95-96, 109-110, 147, 168-181, 191-201."""

    def test_register_admin_sin_body(self, client):
        resp = client.post("/api/v1/auth/register-admin",
                           content_type="application/json")
        assert resp.status_code == 400

    def test_crear_usuario_sin_body(self, client, app):
        with app.app_context():
            u = _u(RolEnum.admin, "auc1")
            h = _hdr(u)
            db.session.commit()
        resp = client.post("/api/v1/auth/usuarios", headers=h,
                           content_type="application/json")
        assert resp.status_code == 400

    def test_editar_mi_perfil(self, client, app):
        with app.app_context():
            u = _u(RolEnum.cliente, "aemp1")
            h = _hdr(u)
            db.session.commit()
        resp = client.put("/api/v1/auth/me", json={"nombre": "X"}, headers=h)
        assert resp.status_code == 200

    def test_editar_usuario(self, client, app):
        with app.app_context():
            a = _u(RolEnum.admin, "aeu1")
            t = _u(RolEnum.cliente, "aeut1")
            ha = _hdr(a)
            tid = t.id
            db.session.commit()
        resp = client.put(f"/api/v1/auth/usuarios/{tid}",
                          json={"nombre": "Y"}, headers=ha)
        assert resp.status_code == 200

    def test_eliminar_usuario_permiso(self, client, app):
        with app.app_context():
            g = _u(RolEnum.gerente, "gestor")
            a = _u(RolEnum.admin, "admgestion")
            h = _hdr(g)
            aid = a.id
            db.session.commit()
        resp = client.delete(f"/api/v1/auth/usuarios/{aid}", headers=h)
        assert resp.status_code == 403

    def test_obtener_usuario_no_encontrado(self, client, app):
        with app.app_context():
            u = _u(RolEnum.admin, "aounf1")
            h = _hdr(u)
            db.session.commit()
        resp = client.get("/api/v1/auth/usuarios/99999", headers=h)
        assert resp.status_code == 404

    def test_obtener_usuario_permiso(self, client, app):
        with app.app_context():
            g = _u(RolEnum.gerente, "aogp1")
            a = _u(RolEnum.admin, "aogpa1")
            h = _hdr(g)
            aid = a.id
            db.session.commit()
        resp = client.get(f"/api/v1/auth/usuarios/{aid}", headers=h)
        assert resp.status_code == 403

    def test_eliminar_mi_cuenta(self, client, app):
        with app.app_context():
            u = _u(RolEnum.cliente, "aemc1")
            h = _hdr(u)
            db.session.commit()
        resp = client.delete("/api/v1/auth/me", headers=h)
        assert resp.status_code == 200


class TestHuespedController:
    """Cubre huesped_controller.py: 30-31, 55-56, 83-89, 103, 115-121."""

    def test_buscar_sin_q(self, client, app):
        with app.app_context():
            u = _u(RolEnum.admin, "hbsq1")
            h = _hdr(u)
            db.session.commit()
        resp = client.get("/api/v1/huespedes/buscar", headers=h)
        assert resp.status_code == 400

    def test_actualizar_sin_body(self, client, app):
        with app.app_context():
            u = _u(RolEnum.admin, "ha1")
            _h(u)
            h = _hdr(u)
            db.session.commit()
        resp = client.put("/api/v1/huespedes/1", headers=h,
                          content_type="application/json")
        assert resp.status_code == 400

    def test_actualizar_lookuperror(self, client, app):
        with app.app_context():
            u = _u(RolEnum.admin, "hal1")
            h = _hdr(u)
            db.session.commit()
        resp = client.put("/api/v1/huespedes/99999",
                          json={"nombre": "X"}, headers=h)
        assert resp.status_code == 404


class TestServicioAdicionalController:
    """Cubre servicio_adicional_controller.py: 37-38, 51-52, 62-66, 89-92, 107-108."""

    def _setup(self, app, tag_extra=""):
        with app.app_context():
            admin = _u(RolEnum.admin, f"s{tag_extra}a1")
            cli = _u(RolEnum.cliente, f"s{tag_extra}c1")
            h = _h(cli)
            hab = _hab(f"S{tag_extra}")
            r = Reserva(
                id_huesped=h.id, id_habitacion=hab.id,
                fecha_entrada=date.today() - timedelta(days=5),
                fecha_salida=date.today() - timedelta(days=3),
                noches=2, subtotal=200000, impuestos=38000, total=238000,
                estado=EstadoReserva.completada,
            )
            db.session.add(r)
            db.session.flush()
            s = ServicioAdicional(
                id_reserva=r.id, tipo=TipoServicio.comedor,
                descripcion="X", costo=10000,
            )
            db.session.add(s)
            db.session.flush()
            hdr = _hdr(admin)
            rid = r.id
            sid = s.id
            db.session.commit()
            return rid, sid, hdr

    def test_agregar_400(self, client, app):
        """ValueError cuando reserva no está Ocupada → 400."""
        with app.app_context():
            admin = _u(RolEnum.admin, "sag400")
            cli = _u(RolEnum.cliente, "sc400")
            h = _h(cli)
            hab = _hab("S400")
            r = Reserva(
                id_huesped=h.id, id_habitacion=hab.id,
                fecha_entrada=date.today() - timedelta(days=5),
                fecha_salida=date.today() - timedelta(days=3),
                noches=2, subtotal=200000, impuestos=38000, total=238000,
                estado=EstadoReserva.completada,
            )
            db.session.add(r)
            db.session.flush()
            hdr = _hdr(admin)
            rid = r.id
            db.session.commit()
        resp = client.post(f"/api/v1/reservas/{rid}/servicios",
                           json={"tipo": "comedor", "descripcion": "X",
                                 "costo": 10000}, headers=hdr)
        assert resp.status_code == 400

    def test_listar_404(self, client, app):
        with app.app_context():
            u = _u(RolEnum.admin, "sl41")
            h = _hdr(u)
            db.session.commit()
        resp = client.get("/api/v1/reservas/99999/servicios", headers=h)
        assert resp.status_code == 404

    def test_obtener_404(self, client, app):
        with app.app_context():
            u = _u(RolEnum.admin, "so41")
            h = _hdr(u)
            db.session.commit()
        resp = client.get("/api/v1/servicios/99999", headers=h)
        assert resp.status_code == 404

    def test_actualizar_404(self, client, app):
        with app.app_context():
            u = _u(RolEnum.admin, "sa41")
            h = _hdr(u)
            db.session.commit()
        resp = client.put("/api/v1/servicios/99999",
                          json={"descripcion": "X"}, headers=h)
        assert resp.status_code == 404

    def test_eliminar_400(self, client, app):
        _, sid, hdr = self._setup(app, "el")
        resp = client.delete(f"/api/v1/servicios/{sid}", headers=hdr)
        assert resp.status_code == 400


class TestReporteController:
    def test_ocupacion_sin_auth(self, client):
        resp = client.get("/api/v1/reportes/ocupacion")
        assert resp.status_code == 401

    def test_ingresos_sin_token(self, client):
        resp = client.get("/api/v1/reportes/ingresos")
        assert resp.status_code == 401

    def test_estadisticas_sin_token(self, client):
        resp = client.get("/api/v1/reportes/estadisticas")
        assert resp.status_code == 401

    def test_ocupacion_fechas_invalidas(self, client, app):
        with app.app_context():
            u = _u(RolEnum.gerente, "rofi1")
            h = _hdr(u)
            db.session.commit()
        resp = client.get(
            "/api/v1/reportes/ocupacion?fecha_inicio=invalida&fecha_fin=invalida",
            headers=h)
        assert resp.status_code == 400

    def test_ingresos_fechas_invalidas(self, client, app):
        with app.app_context():
            u = _u(RolEnum.gerente, "rifi1")
            h = _hdr(u)
            db.session.commit()
        resp = client.get(
            "/api/v1/reportes/ingresos?fecha_inicio=mal&fecha_fin=mal",
            headers=h)
        assert resp.status_code == 400


class TestCheckInCheckOut:
    def test_checkin_404(self, client, app):
        with app.app_context():
            u = _u(RolEnum.admin, "cic1")
            h = _hdr(u)
            db.session.commit()
        resp = client.put("/api/v1/reservas/99999/checkin", headers=h)
        assert resp.status_code == 404