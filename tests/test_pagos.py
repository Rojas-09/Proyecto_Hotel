"""
Tests - Módulo Pagos (RF-13)
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
from app.models.reembolso import (
    EstadoReembolso,
    Reembolso,
)  # noqa: F401 (used in conftest.py)
from app.models.reserva import (
    EstadoReserva,
    Reserva,
)  # noqa: F401 (used in conftest.py)
from app.models.usuario import RolEnum, Usuario

from datetime import date, timedelta


class TestProcesarGarantia:

    def test_garantia_efectivo_exitosa(self, app):
        from app.services.pago_service import procesar_garantia

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_efec_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC1-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"101-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()
            reserva_id = r.id

            resultado = procesar_garantia(reserva_id, "Efectivo")

            assert resultado["tipo"] == "Garantia"
            assert resultado["estado"] == "Pendiente"
            assert resultado["metodo"] == "Efectivo"
            assert float(resultado["monto"]) == pytest.approx(119000.0, rel=1e-2)
            reserva = db.session.get(Reserva, reserva_id)
            assert reserva.estado == EstadoReserva.pendiente

    def test_garantia_reserva_no_encontrada(self, app):
        from app.services.pago_service import procesar_garantia

        with app.app_context():
            with pytest.raises(LookupError):
                procesar_garantia(99999, "Efectivo")

    def test_garantia_tarjeta_mock(self, app):
        from app.services.pago_service import procesar_garantia

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_tarj_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC2-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"102-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()
            reserva_id = r.id

            resultado = procesar_garantia(reserva_id, "Tarjeta", "pm_mock_123")

            assert resultado["estado"] == "Aprobado"
            assert resultado["referencia_externa"].startswith("pi_mock_")

    def test_garantia_duplicada(self, app):
        from app.services.pago_service import procesar_garantia

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_dup_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC3-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"103-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()

            procesar_garantia(r.id, "Tarjeta")
            with pytest.raises(ValueError, match="ya tiene un pago de garantía"):
                procesar_garantia(r.id, "Tarjeta")

    def test_garantia_metodo_invalido(self, app):
        from app.services.pago_service import procesar_garantia

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_inv_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC4-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"104-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()

            with pytest.raises(ValueError, match="Método de pago inválido"):
                procesar_garantia(r.id, "Bitcoin")

    def test_garantia_metodo_vacio(self, app):
        from app.services.pago_service import procesar_garantia

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_ning_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC5-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"105-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()

            with pytest.raises(ValueError, match="obligatorio"):
                procesar_garantia(r.id, None)


class TestConfirmarPagoManual:
    def test_confirmar_efectivo_exitoso(self, app):
        from app.services.pago_service import confirmar_pago_manual, procesar_garantia

        with app.app_context():
            u_admin = Usuario(
                nombre="Admin",
                apellido="T",
                email=f"admin_conf_{id(self)}@test.com",
                rol=RolEnum.admin,
            )
            u_admin.password = "Pass1234!"
            db.session.add(u_admin)
            db.session.flush()

            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"cli_conf_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id,
                documento_id=f"DOC-CONF-{id(self)}",
                tipo_documento="cc",
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"CONF-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()

            pago = procesar_garantia(r.id, "Efectivo")
            assert pago["estado"] == "Pendiente"

            resultado = confirmar_pago_manual(pago["id"], u_admin)
            assert resultado["estado"] == "Aprobado"
            assert resultado["confirmado_por"] == u_admin.id
            assert resultado["fecha_confirmacion"] is not None

            reserva = db.session.get(Reserva, r.id)
            assert reserva.estado == EstadoReserva.confirmada

    def test_confirmar_pago_inexistente(self, app):
        from app.services.pago_service import confirmar_pago_manual

        with app.app_context():
            u = Usuario(
                nombre="Admin",
                apellido="T",
                email=f"adm_{id(self)}@test.com",
                rol=RolEnum.admin,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()
            with pytest.raises(LookupError):
                confirmar_pago_manual(99999, u)

    def test_confirmar_pago_tarjeta_rechazado(self, app):
        from app.services.pago_service import confirmar_pago_manual, procesar_garantia

        with app.app_context():
            u_admin = Usuario(
                nombre="Admin",
                apellido="T",
                email=f"adm_tarj_{id(self)}@test.com",
                rol=RolEnum.admin,
            )
            u_admin.password = "Pass1234!"
            db.session.add(u_admin)
            db.session.flush()
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"cli_tarj_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id,
                documento_id=f"DOC-TARJ-{id(self)}",
                tipo_documento="cc",
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"TARJ-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()

            pago = procesar_garantia(r.id, "Tarjeta")
            assert pago["estado"] == "Aprobado"

            with pytest.raises(
                ValueError, match="Solo pagos en efectivo o transferencia"
            ):
                confirmar_pago_manual(pago["id"], u_admin)


class TestProcesarLiquidacion:

    def test_liquidacion_exitosa(self, app):
        from app.services.pago_service import procesar_liquidacion

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_liq_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC6-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"201-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.pendiente,
            )
            db.session.add(r)
            db.session.commit()

            r.estado = EstadoReserva.confirmada
            r.estado = EstadoReserva.ocupada
            db.session.commit()

            garantia = Pago(
                id_reserva=r.id,
                monto=Decimal("119000"),
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(garantia)
            db.session.commit()

            resultado = procesar_liquidacion(r.id, "Efectivo")
            assert resultado["tipo"] == "Liquidacion"
            assert resultado["estado"] == "Aprobado"

    def test_liquidacion_sin_garantia(self, app):
        from app.services.pago_service import procesar_liquidacion

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_sin_g_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC7-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"202-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.ocupada,
            )
            db.session.add(r)
            db.session.commit()

            with pytest.raises(ValueError, match="pago de garantía"):
                procesar_liquidacion(r.id, "Efectivo")

    def test_liquidacion_reserva_no_ocupada(self, app):
        from app.services.pago_service import procesar_liquidacion

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_no_oc_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC8-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"203-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.confirmada,
            )
            db.session.add(r)
            db.session.commit()

            garantia = Pago(
                id_reserva=r.id,
                monto=Decimal("119000"),
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(garantia)
            db.session.commit()

            with pytest.raises(ValueError, match="no está en estado Ocupada"):
                procesar_liquidacion(r.id, "Efectivo")


class TestSolicitarReembolso:

    def test_reembolso_exitoso(self, app):
        from app.services.pago_service import solicitar_reembolso

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_ref_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC9-{id(self)}", tipo_documento="cc"
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.confirmada,
            )
            db.session.add(r)
            db.session.flush()
            pago = Pago(
                id_reserva=r.id,
                monto=Decimal("119000"),
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(pago)
            db.session.commit()

            resultado = solicitar_reembolso(pago.id, "Cancelación voluntaria")

            assert resultado["estado"] == "Procesado"
            assert resultado["motivo"] == "Cancelación voluntaria"
            db.session.refresh(pago)
            assert pago.estado == EstadoPago.reembolsado

    def test_reembolso_pago_no_encontrado(self, app):
        from app.services.pago_service import solicitar_reembolso

        with app.app_context():
            with pytest.raises(LookupError):
                solicitar_reembolso(99999, "motivo")

    def test_reembolso_duplicado(self, app):
        from app.services.pago_service import solicitar_reembolso

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_dup_ref_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC10-{id(self)}", tipo_documento="cc"
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
                fecha_entrada=date.today() + timedelta(days=5),
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.confirmada,
            )
            db.session.add(r)
            db.session.flush()
            pago = Pago(
                id_reserva=r.id,
                monto=Decimal("119000"),
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(pago)
            db.session.commit()

            solicitar_reembolso(pago.id, "Primera solicitud")
            with pytest.raises(ValueError, match="ya tiene un reembolso"):
                solicitar_reembolso(pago.id, "Segunda solicitud")

    def test_reembolso_sin_motivo(self, app):
        from app.services.pago_service import solicitar_reembolso

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_sm_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC11-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"303-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.confirmada,
            )
            db.session.add(r)
            db.session.flush()
            pago = Pago(
                id_reserva=r.id,
                monto=Decimal("119000"),
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(pago)
            db.session.commit()

            with pytest.raises(ValueError, match="obligatorio"):
                solicitar_reembolso(pago.id, "")


class TestPagoControllerAuth:

    def test_garantia_sin_token(self, client):
        resp = client.post("/api/v1/pagos/garantia/1")
        assert resp.status_code == 401

    def test_liquidacion_sin_token(self, client):
        resp = client.post("/api/v1/pagos/liquidacion/1")
        assert resp.status_code == 401

    def test_obtener_pagos_sin_token(self, client):
        resp = client.get("/api/v1/pagos/reserva/1")
        assert resp.status_code == 401

    def test_reembolso_sin_token(self, client):
        resp = client.post("/api/v1/pagos/reembolso/1")
        assert resp.status_code == 401


class TestPagoControllerRoles:

    def test_liquidacion_cliente_no_permitido(self, client, app):
        from app.utils.jwt_helper import generar_token

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_cli_r_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()
            rol = u.rol.value if hasattr(u.rol, "value") else u.rol
            token = generar_token(u.id, u.email, rol)
        resp = client.post(
            "/api/v1/pagos/liquidacion/1",
            headers={"Authorization": f"Bearer {token}"},
            json={"metodo": "Efectivo"},
        )
        assert resp.status_code == 403

    def test_reembolso_recepcionista_no_permitido(self, client, app):
        from app.utils.jwt_helper import generar_token

        with app.app_context():
            u = Usuario(
                nombre="Recep",
                apellido="T",
                email=f"test_rec_r_{id(self)}@test.com",
                rol=RolEnum.recepcionista,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()
            rol = u.rol.value if hasattr(u.rol, "value") else u.rol
            token = generar_token(u.id, u.email, rol)
        resp = client.post(
            "/api/v1/pagos/reembolso/1",
            headers={"Authorization": f"Bearer {token}"},
            json={"motivo": "test"},
        )
        assert resp.status_code == 403


class TestLiquidacionExtra:

    def test_liquidacion_monto_cero_si_garantia_cubre_todo(self, app):
        """Cuando garantía cubre el total, monto liquidacion = 0."""
        from app.services.pago_service import procesar_liquidacion

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_liq_zero_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC12-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"501-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=6),
                noches=1,
                subtotal=Decimal("100000"),
                impuestos=Decimal("19000"),
                total=Decimal("119000"),
                estado=EstadoReserva.ocupada,
            )
            db.session.add(r)
            db.session.flush()
            garantia = Pago(
                id_reserva=r.id,
                monto=Decimal("119000"),
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(garantia)
            db.session.commit()

            resultado = procesar_liquidacion(r.id, "Efectivo")

            assert resultado["tipo"] == "Liquidacion"
            assert float(resultado["monto"]) == 0.0

    def test_liquidacion_con_servicios_adicionales(self, app):
        """Liquidacion incluye precio de servicios adicionales."""
        from app.services.pago_service import procesar_liquidacion
        from app.models.servicio_adicional import ServicioAdicional, TipoServicio

        with app.app_context():
            u = Usuario(
                nombre="Cli",
                apellido="T",
                email=f"test_liq_serv_{id(self)}@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(
                id_usuario=u.id, documento_id=f"DOC13-{id(self)}", tipo_documento="cc"
            )
            db.session.add(h)
            hab = Habitacion(
                numero=f"502-{id(self)}",
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
                fecha_salida=date.today() + timedelta(days=7),
                noches=2,
                subtotal=Decimal("200000"),
                impuestos=Decimal("38000"),
                total=Decimal("238000"),
                estado=EstadoReserva.ocupada,
            )
            db.session.add(r)
            db.session.flush()
            garantia = Pago(
                id_reserva=r.id,
                monto=Decimal("119000"),
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(garantia)
            servicio = ServicioAdicional(
                id_reserva=r.id,
                tipo=TipoServicio.spa,
                descripcion="Spa test",
                costo=Decimal("50000"),
            )
            db.session.add(servicio)
            db.session.commit()

            resultado = procesar_liquidacion(r.id, "Transferencia")

            assert resultado["tipo"] == "Liquidacion"
            assert resultado["metodo"] == "Transferencia"
