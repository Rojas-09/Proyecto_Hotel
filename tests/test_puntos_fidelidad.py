"""
Tests - Módulo PuntosFidelidad (RF-12)
"""

import pytest
from decimal import Decimal

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.pago import (  # noqa: F401
    EstadoPago,
    MetodoPago,
    Pago,
    TipoPago,
)
from app.models.puntos_fidelidad import PuntosFidelidad
from app.models.reserva import EstadoReserva, Reserva
from app.models.usuario import RolEnum, Usuario
from app.utils.jwt_helper import generar_token

from datetime import date, timedelta


class TestAcreditar:

    def test_acreditar_exito_3_noches(self, app):
        from app.services.puntos_fidelidad_service import acreditar

        with app.app_context():
            u = Usuario(
                nombre="Test",
                apellido="User",
                email=f"test_acred_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC_A_{id(self)}", tipo_documento="CC"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"301-{id(self)}",
                tipo=TipoHabitacion.simple,
                precio_noche=Decimal("100000"),
                capacidad=1,
                estado=EstadoHabitacion.disponible,
            )
            db.session.add(hab)
            db.session.flush()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() + timedelta(days=5),
                fecha_salida=date.today() + timedelta(days=8),
                noches=3,
                subtotal=Decimal("300000"),
                impuestos=Decimal("57000"),
                total=Decimal("357000"),
                estado=EstadoReserva.completada,
            )
            db.session.add(r)
            db.session.commit()

            resultado = acreditar(r.id)

            assert resultado["puntos"] == 30
            assert resultado["id_huesped"] == h.id
            assert resultado["id_reserva"] == r.id
            assert "3 noches" in resultado["concepto"]

    def test_acreditar_exito_1_noche(self, app):
        from app.services.puntos_fidelidad_service import acreditar

        with app.app_context():
            u = Usuario(
                nombre="Test",
                apellido="User",
                email=f"test_1n_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC_1N_{id(self)}", tipo_documento="CC"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"302-{id(self)}",
                tipo=TipoHabitacion.simple,
                precio_noche=Decimal("100000"),
                capacidad=1,
                estado=EstadoHabitacion.disponible,
            )
            db.session.add(hab)
            db.session.flush()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() + timedelta(days=1),
                fecha_salida=date.today() + timedelta(days=2),
                noches=1,
                subtotal=Decimal("100000"),
                impuestos=Decimal("19000"),
                total=Decimal("119000"),
                estado=EstadoReserva.completada,
            )
            db.session.add(r)
            db.session.commit()

            resultado = acreditar(r.id)

            assert resultado["puntos"] == 10
            assert "1 noche" in resultado["concepto"]

    def test_acreditar_duplicado(self, app):
        from app.services.puntos_fidelidad_service import acreditar

        with app.app_context():
            u = Usuario(
                nombre="Test",
                apellido="User",
                email=f"test_dup_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC_DUP_{id(self)}", tipo_documento="CC"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"303-{id(self)}",
                tipo=TipoHabitacion.doble,
                precio_noche=Decimal("150000"),
                capacidad=2,
                estado=EstadoHabitacion.disponible,
            )
            db.session.add(hab)
            db.session.flush()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() + timedelta(days=10),
                fecha_salida=date.today() + timedelta(days=13),
                noches=3,
                subtotal=Decimal("450000"),
                impuestos=Decimal("85500"),
                total=Decimal("535500"),
                estado=EstadoReserva.completada,
            )
            db.session.add(r)
            db.session.commit()

            acreditar(r.id)
            with pytest.raises(ValueError, match="[Yy]a se acreditaron"):
                acreditar(r.id)

    def test_acreditar_reserva_no_existe(self, app):
        from app.services.puntos_fidelidad_service import acreditar

        with app.app_context():
            with pytest.raises(LookupError):
                acreditar(99999)


class TestObtenerTotal:

    def test_obtener_total_sin_puntos(self, app):
        from app.services.puntos_fidelidad_service import obtener_total

        with app.app_context():
            u = Usuario(
                nombre="Test",
                apellido="User",
                email=f"test_tot_0_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC_T0_{id(self)}", tipo_documento="CC"
            )
            db.session.add(h)
            db.session.commit()

            total = obtener_total(h.id)
            assert total == 0

    def test_obtener_total_varios_registros(self, app):
        from app.services.puntos_fidelidad_service import obtener_total

        with app.app_context():
            u = Usuario(
                nombre="Test",
                apellido="User",
                email=f"test_tot_m_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC_TM_{id(self)}", tipo_documento="CC"
            )
            db.session.add(h)
            hab1 = Habitacion(
                numero=f"401-{id(self)}",
                tipo=TipoHabitacion.simple,
                precio_noche=Decimal("100000"),
                capacidad=1,
                estado=EstadoHabitacion.disponible,
            )
            hab2 = Habitacion(
                numero=f"402-{id(self)}",
                tipo=TipoHabitacion.doble,
                precio_noche=Decimal("150000"),
                capacidad=2,
                estado=EstadoHabitacion.disponible,
            )
            db.session.add(hab1)
            db.session.add(hab2)
            db.session.flush()
            r1 = Reserva(
                id_huesped=h.id,
                id_habitacion=hab1.id,
                fecha_entrada=date.today() + timedelta(days=1),
                fecha_salida=date.today() + timedelta(days=3),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.completada,
            )
            r2 = Reserva(
                id_huesped=h.id,
                id_habitacion=hab2.id,
                fecha_entrada=date.today() + timedelta(days=10),
                fecha_salida=date.today() + timedelta(days=14),
                noches=4,
                subtotal=Decimal("600000"),
                impuestos=Decimal("114000"),
                total=Decimal("714000"),
                estado=EstadoReserva.completada,
            )
            db.session.add(r1)
            db.session.add(r2)
            db.session.commit()

            db.session.add(
                PuntosFidelidad(
                    id_huesped=h.id,
                    id_reserva=r1.id,
                    puntos=20,
                    concepto="10 puntos x 2 noches",
                )
            )
            db.session.add(
                PuntosFidelidad(
                    id_huesped=h.id,
                    id_reserva=r2.id,
                    puntos=40,
                    concepto="10 puntos x 4 noches",
                )
            )
            db.session.commit()

            total = obtener_total(h.id)
            assert total == 60

    def test_obtener_total_huesped_no_existe(self, app):
        from app.services.puntos_fidelidad_service import obtener_total

        with app.app_context():
            with pytest.raises(LookupError):
                obtener_total(99999)


class TestListarHistorial:

    def test_listar_historial_vacio(self, app):
        from app.services.puntos_fidelidad_service import listar_historial

        with app.app_context():
            u = Usuario(
                nombre="Test",
                apellido="User",
                email=f"test_hist_v_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC_HV_{id(self)}", tipo_documento="CC"
            )
            db.session.add(h)
            db.session.commit()

            historial = listar_historial(h.id)
            assert historial == []

    def test_listar_historial_con_datos(self, app):
        from app.services.puntos_fidelidad_service import listar_historial

        with app.app_context():
            u = Usuario(
                nombre="Test",
                apellido="User",
                email=f"test_hist_d_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC_HD_{id(self)}", tipo_documento="CC"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"501-{id(self)}",
                tipo=TipoHabitacion.suite,
                precio_noche=Decimal("200000"),
                capacidad=2,
                estado=EstadoHabitacion.disponible,
            )
            db.session.add(hab)
            db.session.flush()
            r = Reserva(
                id_huesped=h.id,
                id_habitacion=hab.id,
                fecha_entrada=date.today() + timedelta(days=5),
                fecha_salida=date.today() + timedelta(days=8),
                noches=3,
                subtotal=Decimal("600000"),
                impuestos=Decimal("114000"),
                total=Decimal("714000"),
                estado=EstadoReserva.completada,
            )
            db.session.add(r)
            db.session.commit()

            registro = PuntosFidelidad(
                id_huesped=h.id,
                id_reserva=r.id,
                puntos=30,
                concepto="10 puntos x 3 noches",
            )
            db.session.add(registro)
            db.session.commit()

            historial = listar_historial(h.id)
            assert len(historial) == 1
            assert historial[0]["puntos"] == 30
            assert historial[0]["id_reserva"] == r.id

    def test_listar_historial_huesped_no_existe(self, app):
        from app.services.puntos_fidelidad_service import listar_historial

        with app.app_context():
            with pytest.raises(LookupError):
                listar_historial(99999)


class TestPuntosControllerAuth:

    def test_obtener_total_sin_token(self, client):
        resp = client.get("/api/v1/huespedes/1/puntos")
        assert resp.status_code == 401

    def test_historial_sin_token(self, client):
        resp = client.get("/api/v1/huespedes/1/puntos/historial")
        assert resp.status_code == 401


class TestPuntosControllerRoles:

    def test_obtener_total_con_cliente_denegado(self, app, client):
        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_cli_pt_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()
            rol = u.rol.value if hasattr(u.rol, "value") else u.rol
            token = generar_token(u.id, u.email, rol)
        resp = client.get(
            "/api/v1/huespedes/1/puntos", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403

    def test_obtener_total_con_recepcionista_exito(self, app, client):
        with app.app_context():
            u = Usuario(
                nombre="Recep",
                apellido="T",
                email=f"test_rec_pt_{id(self)}@test.com",
                rol=RolEnum.recepcionista,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id,
                documento_id=f"DOC_RECEP_{id(self)}",
                tipo_documento="CC",
            )
            db.session.add(h)
            db.session.commit()
            huesped_id = h.id
            rol = u.rol.value if hasattr(u.rol, "value") else u.rol
            token = generar_token(u.id, u.email, rol)
        resp = client.get(
            f"/api/v1/huespedes/{huesped_id}/puntos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "total" in data["data"]

    def test_obtener_total_huesped_no_encontrado(self, app, client):
        with app.app_context():
            u = Usuario(
                nombre="Recep",
                apellido="T",
                email=f"test_404_pt_{id(self)}@test.com",
                rol=RolEnum.recepcionista,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()
            rol = u.rol.value if hasattr(u.rol, "value") else u.rol
            token = generar_token(u.id, u.email, rol)
        resp = client.get(
            "/api/v1/huespedes/99999/puntos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_historial_exito(self, app, client):
        with app.app_context():
            u = Usuario(
                nombre="Recep",
                apellido="T",
                email=f"test_hist_c_{id(self)}@test.com",
                rol=RolEnum.recepcionista,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id,
                documento_id=f"DOC_HIST_{id(self)}",
                tipo_documento="CC",
            )
            db.session.add(h)
            db.session.commit()
            huesped_id = h.id
            rol = u.rol.value if hasattr(u.rol, "value") else u.rol
            token = generar_token(u.id, u.email, rol)
        resp = client.get(
            f"/api/v1/huespedes/{huesped_id}/puntos/historial",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "historial" in data["data"]
        assert "total" in data["data"]


class _DataHelper:
    """Crea datos de prueba y retorna solo ids/tokens (no ORM objects)."""

    @staticmethod
    def crear_huesped_con_puntos(email_sufix: str, puntos=500):
        u = Usuario(
            nombre="Cli", apellido="T",
            email=f"pfc_canj_{email_sufix}@test.com",
            rol=RolEnum.cliente,
        )
        u.password = "Pass1234!"
        db.session.add(u)
        db.session.flush()
        h = Huesped(
            id_usuario=u.id,
            documento_id=f"DOC_CANJ_{email_sufix}",
            tipo_documento="CC",
        )
        db.session.add(h)
        hab = Habitacion(
            numero=f"PF-{email_sufix}", tipo=TipoHabitacion.simple,
            precio_noche=Decimal("100000"), capacidad=1,
            estado=EstadoHabitacion.disponible,
        )
        db.session.add(hab)
        db.session.flush()
        r = Reserva(
            id_huesped=h.id, id_habitacion=hab.id,
            fecha_entrada=date.today() + timedelta(days=1),
            fecha_salida=date.today() + timedelta(days=(puntos // 10) + 1),
            noches=puntos // 10, subtotal=Decimal("100000"),
            impuestos=Decimal("19000"), total=Decimal("119000"),
            estado=EstadoReserva.completada,
        )
        db.session.add(r)
        db.session.commit()
        db.session.add(PuntosFidelidad(
            id_huesped=h.id, id_reserva=r.id,
            puntos=puntos, concepto=f"{puntos} pts",
        ))
        db.session.commit()
        token = generar_token(u.id, u.email, "cliente")
        return h.id, token


class TestListarCanjeos:
    def test_exito(self, app, client):
        with app.app_context():
            cli = Usuario(
                nombre="Cli", apellido="T",
                email=f"pfc_list_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            cli.password = "Pass1234!"
            db.session.add(cli)
            db.session.flush()
            h = Huesped(
                id_usuario=cli.id,
                documento_id=f"DOC_CLI_{id(self)}",
                tipo_documento="CC",
            )
            db.session.add(h)
            db.session.commit()
            token = generar_token(cli.id, cli.email, "cliente")
            hid = h.id
        resp = client.get(
            f"/api/v1/huespedes/{hid}/puntos/canjeos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]["canjeos"]) == 5


class TestHistorialLookupError:
    def test_huesped_inexistente_retorna_404(self, app, client):
        with app.app_context():
            u = Usuario(
                nombre="Admin", apellido="T",
                email=f"pfc_hist404_{id(self)}@test.com",
                rol=RolEnum.admin,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.get(
            "/api/v1/huespedes/99999/puntos/historial",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestCanjear:
    def test_sin_opcion_id_retorna_400(self, app, client):
        with app.app_context():
            hid, token = _DataHelper.crear_huesped_con_puntos("no_op")
        resp = client.post(
            f"/api/v1/huespedes/{hid}/puntos/canjear",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert "opcion_id" in resp.get_json()["mensaje"]

    def test_opcion_invalida_retorna_400(self, app, client):
        with app.app_context():
            hid, token = _DataHelper.crear_huesped_con_puntos("bad_op")
        resp = client.post(
            f"/api/v1/huespedes/{hid}/puntos/canjear",
            json={"opcion_id": 99},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_huesped_no_existe_retorna_404(self, app, client):
        with app.app_context():
            u = Usuario(
                nombre="Admin", apellido="T",
                email=f"pfc_404_{id(self)}@test.com",
                rol=RolEnum.admin,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()
            token = generar_token(u.id, u.email, "admin")
        resp = client.post(
            "/api/v1/huespedes/99999/puntos/canjear",
            json={"opcion_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_puntos_insuficientes_retorna_400(self, app, client):
        with app.app_context():
            hid, token = _DataHelper.crear_huesped_con_puntos("no_pts", puntos=10)
        resp = client.post(
            f"/api/v1/huespedes/{hid}/puntos/canjear",
            json={"opcion_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_canjear_exitoso_retorna_200(self, app, client):
        with app.app_context():
            hid, token = _DataHelper.crear_huesped_con_puntos("ok", puntos=500)
        resp = client.post(
            f"/api/v1/huespedes/{hid}/puntos/canjear",
            json={"opcion_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["canje"]["puntos"] == -100
        assert data["data"]["puntos_restantes"] == 400


class TestOwnershipPuntos:
    def test_cliente_canjear_sus_propios_puntos_exito(self, app, client):
        with app.app_context():
            hid, token = _DataHelper.crear_huesped_con_puntos("own_ok", puntos=500)
        resp = client.post(
            f"/api/v1/huespedes/{hid}/puntos/canjear",
            json={"opcion_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    def test_cliente_canjear_puntos_de_otro_huesped_retorna_403(self, app, client):
        with app.app_context():
            u_cliente = Usuario(
                nombre="Cli", apellido="T",
                email=f"pfc_own403_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u_cliente.password = "Pass1234!"
            db.session.add(u_cliente)
            db.session.flush()
            h_propio = Huesped(
                id_usuario=u_cliente.id,
                documento_id="DOC_OWN_CLI",
                tipo_documento="CC",
            )
            db.session.add(h_propio)
            u_otro = Usuario(
                nombre="Otro", apellido="T",
                email=f"pfc_otro_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u_otro.password = "Pass1234!"
            db.session.add(u_otro)
            db.session.flush()
            h_otro = Huesped(
                id_usuario=u_otro.id,
                documento_id="DOC_OTRO",
                tipo_documento="CC",
            )
            db.session.add(h_otro)
            db.session.commit()
            token = generar_token(u_cliente.id, u_cliente.email, "cliente")
            otro_hid = h_otro.id
        resp = client.post(
            f"/api/v1/huespedes/{otro_hid}/puntos/canjear",
            json={"opcion_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
