"""
Tests del módulo ServicioAdicional — RF-10 (Comedor) y RF-11 (Spa)
"""
from decimal import Decimal

import pytest

from app import db
from app.models.factura import EstadoFactura, Factura
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app.models.reserva import EstadoReserva, Reserva
from app.models.servicio_adicional import ServicioAdicional, TipoServicio
from app.models.usuario import RolEnum, Usuario
from app.utils.fecha_helper import ahora_colombia
from app.utils.jwt_helper import generar_token


def _usuario(rol: RolEnum, tag: str) -> Usuario:
    u = Usuario(
        nombre="Test",
        apellido=f"{tag}",
        email=f"{tag}_{id(tag)}@hotel.com",
        rol=rol,
    )
    u.password = "Pass1234!"
    db.session.add(u)
    db.session.flush()
    return u


def _huesped(usuario: Usuario) -> Huesped:
    h = Huesped(
        id_usuario=usuario.id,
        documento_id=f"CC{hash(str(usuario.id)) % 100000:05d}",
        tipo_documento="CC",
    )
    db.session.add(h)
    db.session.flush()
    return h


def _habitacion() -> Habitacion:
    import random
    hab = Habitacion(
        numero=f"{random.randint(8000, 9999)}",
        tipo=TipoHabitacion.doble,
        precio_noche=Decimal("100000.00"),
        capacidad=2,
        estado=EstadoHabitacion.disponible,
    )
    db.session.add(hab)
    db.session.flush()
    return hab


def _reserva(huesped: Huesped, hab: Habitacion,
             estado: EstadoReserva = EstadoReserva.ocupada) -> Reserva:
    from datetime import date, timedelta
    hoy = date.today()
    r = Reserva(
        id_huesped=huesped.id,
        id_habitacion=hab.id,
        fecha_entrada=hoy,
        fecha_salida=hoy + timedelta(days=2),
        noches=2,
        subtotal=Decimal("168067.23"),
        impuestos=Decimal("31932.77"),
        total=Decimal("200000.00"),
        estado=estado,
    )
    db.session.add(r)
    db.session.flush()
    return r


def _servicio(reserva: Reserva, tipo=TipoServicio.comedor,
              costo="15000.00") -> ServicioAdicional:
    s = ServicioAdicional(
        id_reserva=reserva.id,
        tipo=tipo,
        descripcion="Servicio test",
        costo=Decimal(costo),
        fecha_hora=ahora_colombia(),
    )
    db.session.add(s)
    db.session.flush()
    return s


def _factura_emitida(reserva: Reserva) -> Factura:
    f = Factura(
        id_reserva=reserva.id,
        subtotal=Decimal("168067.23"),
        impuestos=Decimal("31932.77"),
        servicios_adicionales_total=Decimal("0"),
        total=Decimal("200000.00"),
        estado=EstadoFactura.emitida,
        fecha_emision=ahora_colombia(),
    )
    db.session.add(f)
    db.session.flush()
    return f


def _token(usuario: Usuario) -> dict:
    rol = usuario.rol.value if hasattr(usuario.rol, "value") else usuario.rol
    tok = generar_token(usuario.id, usuario.email, rol)
    return {"Authorization": f"Bearer {tok}"}


class TestAgregarServicio:

    def test_agregar_comedor_exitoso(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag1")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            resultado = svc.agregar(rid, "Comedor", "Desayuno continental", "15000")

            assert resultado["tipo"] == "Comedor"
            assert resultado["costo"] == 15000.0

    def test_agregar_spa_exitoso(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag2")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            resultado = svc.agregar(rid, "Spa", "Masaje relajante 60 min", "80000")

            assert resultado["tipo"] == "Spa"

    def test_agregar_lavanderia(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag3")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            resultado = svc.agregar(rid, "Lavanderia", "Lavado 3 prendas", "20000")

            assert resultado["tipo"] == "Lavanderia"

    def test_reserva_no_encontrada(self, app):
        with app.app_context():
            from app.services import servicio_adicional_service as svc
            with pytest.raises(LookupError, match="no encontrada"):
                svc.agregar(99999, "Comedor", "Desayuno", "15000")

    def test_reserva_no_ocupada_pendiente(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag5")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab, EstadoReserva.pendiente)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="Ocupada"):
                svc.agregar(rid, "Comedor", "Desayuno", "15000")

    def test_reserva_completada_rechaza(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag6")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab, EstadoReserva.completada)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="Ocupada"):
                svc.agregar(rid, "Spa", "Masaje", "80000")

    def test_factura_emitida_rechaza(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag7")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            _factura_emitida(r)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="factura emitida"):
                svc.agregar(rid, "Comedor", "Desayuno", "15000")

    def test_tipo_invalido(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag8")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="inválido"):
                svc.agregar(rid, "Discoteca", "Fiesta", "50000")

    def test_tipo_none(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag9")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="obligatorio"):
                svc.agregar(rid, None, "Desayuno", "15000")

    def test_costo_cero_rechaza(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag10")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="mayor que cero"):
                svc.agregar(rid, "Comedor", "Desayuno", "0")

    def test_costo_negativo_rechaza(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag11")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="mayor que cero"):
                svc.agregar(rid, "Spa", "Masaje", "-100")

    def test_costo_none_rechaza(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag12")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="obligatorio"):
                svc.agregar(rid, "Comedor", "Desayuno", None)

    def test_descripcion_vacia_rechaza(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_ag13")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="descripción"):
                svc.agregar(rid, "Comedor", "   ", "15000")


class TestListarServicios:

    def test_listar_vacio(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_lst1")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            resultado = svc.listar(rid)

            assert resultado["servicios"] == []
            assert resultado["total"] == 0
            assert resultado["subtotal"] == 0.0

    def test_listar_con_servicios(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_lst2")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            _servicio(r, TipoServicio.comedor, "15000.00")
            _servicio(r, TipoServicio.spa, "80000.00")
            db.session.commit()
            rid = r.id

            from app.services import servicio_adicional_service as svc
            resultado = svc.listar(rid)

            assert resultado["total"] == 2
            assert resultado["subtotal"] == 95000.0

    def test_listar_reserva_no_existe(self, app):
        with app.app_context():
            from app.services import servicio_adicional_service as svc
            with pytest.raises(LookupError):
                svc.listar(99999)


class TestEliminarServicio:

    def test_eliminar_exitoso(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_del1")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            s = _servicio(r)
            db.session.commit()
            sid = s.id

            from app.services import servicio_adicional_service as svc
            resultado = svc.eliminar(sid)

            assert resultado["id"] == sid

    def test_eliminar_no_existe(self, app):
        with app.app_context():
            from app.services import servicio_adicional_service as svc
            with pytest.raises(LookupError):
                svc.eliminar(99999)

    def test_eliminar_con_factura_emitida(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_del2")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            s = _servicio(r)
            _factura_emitida(r)
            db.session.commit()
            sid = s.id

            from app.services import servicio_adicional_service as svc
            with pytest.raises(ValueError, match="factura emitida"):
                svc.eliminar(sid)


class TestActualizarServicio:

    def test_actualizar_costo(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_upd1")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            s = _servicio(r, costo="15000.00")
            db.session.commit()
            sid = s.id

            from app.services import servicio_adicional_service as svc
            resultado = svc.actualizar(sid, costo_raw="20000")

            assert resultado["costo"] == 20000.0

    def test_actualizar_descripcion(self, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_upd2")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            s = _servicio(r)
            db.session.commit()
            sid = s.id

            from app.services import servicio_adicional_service as svc
            resultado = svc.actualizar(sid, descripcion="Nueva descripción")

            assert resultado["descripcion"] == "Nueva descripción"

    def test_actualizar_no_existe(self, app):
        with app.app_context():
            from app.services import servicio_adicional_service as svc
            with pytest.raises(LookupError):
                svc.actualizar(99999, costo_raw="100")


class TestServicioControllerAuth:

    def test_agregar_sin_token(self, client):
        resp = client.post("/api/v1/reservas/1/servicios", json={})
        assert resp.status_code == 401

    def test_listar_sin_token(self, client):
        resp = client.get("/api/v1/reservas/1/servicios")
        assert resp.status_code == 401

    def test_obtener_sin_token(self, client):
        resp = client.get("/api/v1/servicios/1")
        assert resp.status_code == 401

    def test_actualizar_sin_token(self, client):
        resp = client.put("/api/v1/servicios/1", json={})
        assert resp.status_code == 401

    def test_eliminar_sin_token(self, client):
        resp = client.delete("/api/v1/servicios/1")
        assert resp.status_code == 401


class TestServicioControllerRoles:

    def test_cliente_no_puede_agregar(self, client, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_rol1")
            db.session.commit()
            headers = _token(u)

        resp = client.post(
            "/api/v1/reservas/1/servicios",
            json={"tipo": "Comedor", "descripcion": "test", "costo": 10000},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_cliente_no_puede_eliminar(self, client, app):
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_rol2")
            db.session.commit()
            headers = _token(u)

        resp = client.delete("/api/v1/servicios/1", headers=headers)
        assert resp.status_code == 403

    def test_recepcionista_no_puede_eliminar(self, client, app):
        with app.app_context():
            u = _usuario(RolEnum.recepcionista, "rec_rol1")
            db.session.commit()
            headers = _token(u)

        resp = client.delete("/api/v1/servicios/1", headers=headers)
        assert resp.status_code == 403


class TestServicioControllerEndpoints:

    def test_post_agregar_exitoso(self, client, app):
        with app.app_context():
            rec = _usuario(RolEnum.recepcionista, "rec_ep1")
            u_cli = _usuario(RolEnum.cliente, "cli_ep1")
            h = _huesped(u_cli)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            headers = _token(rec)
            rid = r.id

        resp = client.post(
            f"/api/v1/reservas/{rid}/servicios",
            json={"tipo": "Comedor", "descripcion": "Almuerzo ejecutivo", "costo": 25000},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["servicio"]["tipo"] == "Comedor"

    def test_post_reserva_no_existe(self, client, app):
        with app.app_context():
            rec = _usuario(RolEnum.recepcionista, "rec_ep2")
            db.session.commit()
            headers = _token(rec)

        resp = client.post(
            "/api/v1/reservas/99999/servicios",
            json={"tipo": "Spa", "descripcion": "Masaje", "costo": 80000},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_post_tipo_invalido(self, client, app):
        with app.app_context():
            rec = _usuario(RolEnum.recepcionista, "rec_ep3")
            u_cli = _usuario(RolEnum.cliente, "cli_ep3")
            h = _huesped(u_cli)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            headers = _token(rec)
            rid = r.id

        resp = client.post(
            f"/api/v1/reservas/{rid}/servicios",
            json={"tipo": "Karaoke", "descripcion": "Noche musical", "costo": 50000},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "inválido" in resp.get_json()["error"].lower()

    def test_get_listar_exitoso(self, client, app):
        with app.app_context():
            rec = _usuario(RolEnum.recepcionista, "rec_ep4")
            u_cli = _usuario(RolEnum.cliente, "cli_ep4")
            h = _huesped(u_cli)
            hab = _habitacion()
            r = _reserva(h, hab)
            _servicio(r, TipoServicio.spa, "80000.00")
            db.session.commit()
            headers = _token(rec)
            rid = r.id

        resp = client.get(f"/api/v1/reservas/{rid}/servicios", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert data["subtotal"] == 80000.0

    def test_put_actualizar_exitoso(self, client, app):
        with app.app_context():
            rec = _usuario(RolEnum.recepcionista, "rec_ep5")
            u_cli = _usuario(RolEnum.cliente, "cli_ep5")
            h = _huesped(u_cli)
            hab = _habitacion()
            r = _reserva(h, hab)
            s = _servicio(r, costo="15000.00")
            db.session.commit()
            headers = _token(rec)
            sid = s.id

        resp = client.put(
            f"/api/v1/servicios/{sid}",
            json={"costo": 18000},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["servicio"]["costo"] == 18000.0

    def test_delete_exitoso(self, client, app):
        with app.app_context():
            adm = _usuario(RolEnum.admin, "adm_ep1")
            u_cli = _usuario(RolEnum.cliente, "cli_ep6")
            h = _huesped(u_cli)
            hab = _habitacion()
            r = _reserva(h, hab)
            s = _servicio(r)
            db.session.commit()
            headers = _token(adm)
            sid = s.id

        resp = client.delete(f"/api/v1/servicios/{sid}", headers=headers)
        assert resp.status_code == 200
        assert "eliminado" in resp.get_json()["mensaje"].lower()

    def test_delete_no_existe(self, client, app):
        with app.app_context():
            adm = _usuario(RolEnum.admin, "adm_ep2")
            db.session.commit()
            headers = _token(adm)

        resp = client.delete("/api/v1/servicios/99999", headers=headers)
        assert resp.status_code == 404

    def test_post_costo_cero(self, client, app):
        with app.app_context():
            rec = _usuario(RolEnum.recepcionista, "rec_ep6")
            u_cli = _usuario(RolEnum.cliente, "cli_ep7")
            h = _huesped(u_cli)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            headers = _token(rec)
            rid = r.id

        resp = client.post(
            f"/api/v1/reservas/{rid}/servicios",
            json={"tipo": "Comedor", "descripcion": "Gratis", "costo": 0},
            headers=headers,
        )
        assert resp.status_code == 400