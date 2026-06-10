"""
Tests — RF-13 M1 (Webhook), M2 (Reintento), M3 (Auto-expiro)
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta, datetime

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app.models.reserva import EstadoReserva, Reserva
from app.models.usuario import RolEnum, Usuario
from app.utils.fecha_helper import ahora_colombia


def _crear_cliente_y_reserva(app, seed: str, estado=EstadoReserva.pendiente):
    u = Usuario(
        nombre="Cli", apellido="T",
        email=f"rf13_{seed}@test.com",
        rol=RolEnum.cliente,
    )
    u.password = "Pass1234!"
    db.session.add(u)
    db.session.flush()
    h = Huesped(id_usuario=u.id, documento_id=f"RF13-{seed}", tipo_documento="cc")
    db.session.add(h)
    hab = Habitacion(
        numero=f"RF13-{seed}", tipo=TipoHabitacion.simple,
        precio_noche=Decimal("100000"), capacidad=1,
        estado=EstadoHabitacion.disponible,
    )
    db.session.add(hab)
    db.session.flush()
    r = Reserva(
        id_huesped=h.id, id_habitacion=hab.id,
        fecha_entrada=date.today() + timedelta(days=5),
        fecha_salida=date.today() + timedelta(days=7),
        noches=2, subtotal=Decimal("200000"),
        impuestos=Decimal("38000"), total=Decimal("238000"),
        estado=estado,
    )
    db.session.add(r)
    db.session.commit()
    return r, hab


# ===================================================================
# M1 — Webhook
# ===================================================================


class TestWebhookEventos:

    def test_webhook_sin_firma_retorna_400(self, client, app):
        resp = client.post(
            "/api/v1/pagos/webhook",
            data=b"{}",
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["procesado"] is False

    def test_webhook_payment_failed_crea_rechazado(self, app):
        from app.services.stripe_webhook_service import _manejar_payment_failed
        with app.app_context():
            r, hab = _crear_cliente_y_reserva(app, "wh_fail")
            pago = Pago(
                id_reserva=r.id, monto=Decimal("119000"),
                metodo=MetodoPago.tarjeta, tipo=TipoPago.garantia,
                estado=EstadoPago.pendiente,
                stripe_payment_intent_id="pi_test_failed_1",
            )
            db.session.add(pago)
            db.session.commit()

            objeto = {
                "id": "pi_test_failed_1",
                "last_payment_error": {
                    "message": "Tu tarjeta no tiene fondos suficientes.",
                },
            }
            resultado = _manejar_payment_failed(objeto)
            db.session.commit()

            assert "rechazado" in resultado
            db.session.refresh(pago)
            assert pago.estado == EstadoPago.rechazado
            assert "fondos" in pago.failure_message

    def test_webhook_payment_succeeded_confirma(self, app):
        from app.services.stripe_webhook_service import _manejar_payment_succeeded
        with app.app_context():
            r, hab = _crear_cliente_y_reserva(app, "wh_succ")
            pago = Pago(
                id_reserva=r.id, monto=Decimal("119000"),
                metodo=MetodoPago.tarjeta, tipo=TipoPago.garantia,
                estado=EstadoPago.pendiente,
                stripe_payment_intent_id="pi_test_succ_1",
            )
            db.session.add(pago)
            db.session.commit()

            objeto = {"id": "pi_test_succ_1"}
            resultado = _manejar_payment_succeeded(objeto)
            db.session.commit()

            assert "confirmado" in resultado
            db.session.refresh(pago)
            assert pago.estado == EstadoPago.aprobado

    def test_webhook_charge_refunded_marca_reembolsado(self, app):
        from app.services.stripe_webhook_service import _manejar_charge_refunded
        with app.app_context():
            r, hab = _crear_cliente_y_reserva(app, "wh_ref")
            pago = Pago(
                id_reserva=r.id, monto=Decimal("119000"),
                metodo=MetodoPago.tarjeta, tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
                stripe_payment_intent_id="pi_test_ref_1",
            )
            db.session.add(pago)
            db.session.commit()

            objeto = {
                "payment_intent": "pi_test_ref_1",
                "amount_refunded": 11900000,
            }
            resultado = _manejar_charge_refunded(objeto)
            db.session.commit()

            assert "reembolsado" in resultado
            db.session.refresh(pago)
            assert pago.estado == EstadoPago.reembolsado
            assert pago.reembolso is not None


# ===================================================================
# M2 — Reintento
# ===================================================================


class TestReintentoGarantia:

    def test_reintento_tras_rechazo_permite_nuevo_pago(self, app):
        from app.services.pago_service import procesar_garantia
        with app.app_context():
            r, hab = _crear_cliente_y_reserva(app, "retry1")

            pago_rechazado = Pago(
                id_reserva=r.id, monto=Decimal("119000"),
                metodo=MetodoPago.tarjeta, tipo=TipoPago.garantia,
                estado=EstadoPago.rechazado,
                failure_message="Tarjeta rechazada: fondos insuficientes",
                stripe_payment_intent_id="pi_fail_retry",
            )
            db.session.add(pago_rechazado)
            db.session.commit()

            resultado = procesar_garantia(r.id, "Efectivo")
            assert resultado["tipo"] == "Garantia"
            assert resultado["estado"] == "Pendiente"
            assert resultado["metodo"] == "Efectivo"

    def test_reintento_bloqueado_si_hay_aprobada(self, app):
        from app.services.pago_service import procesar_garantia
        with app.app_context():
            r, hab = _crear_cliente_y_reserva(app, "retry2")

            pago_ok = Pago(
                id_reserva=r.id, monto=Decimal("119000"),
                metodo=MetodoPago.efectivo, tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(pago_ok)
            db.session.commit()

            with pytest.raises(ValueError, match="ya tiene un pago de garantía"):
                procesar_garantia(r.id, "Efectivo")

    def test_idempotency_key_dinamica(self, app):
        from app.services.pago_service import _cobrar_stripe
        with app.app_context():
            ref1 = _cobrar_stripe(Decimal("10000"), "pm_mock", 1, "garantia")
            ref2 = _cobrar_stripe(Decimal("10000"), "pm_mock", 1, "garantia")
            assert ref1 != ref2


# ===================================================================
# M3 — Auto-expiro
# ===================================================================


class TestAutoExpiro:

    def test_limpiar_expiradas_cancela_vencidas(self, app):
        from app.services.reserva_service import limpiar_expiradas
        with app.app_context():
            pasado = ahora_colombia() - timedelta(minutes=10)

            r1, hab1 = _crear_cliente_y_reserva(app, "exp1")
            r1.expira_en = pasado
            db.session.commit()

            r2, hab2 = _crear_cliente_y_reserva(app, "exp2")
            r2.expira_en = pasado
            db.session.commit()

            cantidad = limpiar_expiradas()

            assert cantidad == 2
            db.session.refresh(r1)
            db.session.refresh(r2)
            assert r1.estado == EstadoReserva.cancelada
            assert r2.estado == EstadoReserva.cancelada
            assert "Auto-expirada" in r1.motivo_cancelacion

    def test_limpiar_expiradas_ignora_futuras(self, app):
        from app.services.reserva_service import limpiar_expiradas
        with app.app_context():
            futuro = ahora_colombia() + timedelta(minutes=60)
            r, hab = _crear_cliente_y_reserva(app, "exp4")
            r.expira_en = futuro
            db.session.commit()

            cantidad = limpiar_expiradas()
            assert cantidad == 0
            db.session.refresh(r)
            assert r.estado == EstadoReserva.pendiente

    def test_limpiar_expiradas_ignora_no_pendientes(self, app):
        from app.services.reserva_service import limpiar_expiradas
        with app.app_context():
            pasado = ahora_colombia() - timedelta(minutes=10)
            r, hab = _crear_cliente_y_reserva(
                app, "exp5", estado=EstadoReserva.confirmada
            )
            r.expira_en = pasado
            db.session.commit()

            cantidad = limpiar_expiradas()
            assert cantidad == 0
            db.session.refresh(r)
            assert r.estado == EstadoReserva.confirmada

    def test_limpiar_expiradas_endpoint(self, client, app):
        from app.utils.jwt_helper import generar_token
        with app.app_context():
            u = Usuario(
                nombre="Admin", apellido="T",
                email="exp_admin@test.com",
                rol=RolEnum.admin,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.commit()
            token = generar_token(
                u.id, u.email,
                u.rol.value if hasattr(u.rol, "value") else u.rol,
            )

        resp = client.post(
            "/api/v1/reservas/limpiar-expiradas",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_limpiar_expiradas_sin_autenticacion(self, client):
        resp = client.post("/api/v1/reservas/limpiar-expiradas")
        assert resp.status_code == 401

    def test_crear_reserva_asigna_expira_en(self, app):
        from app.services.reserva_service import crear
        with app.app_context():
            u = Usuario(
                nombre="Cli", apellido="T",
                email="exp_crear@test.com",
                rol=RolEnum.cliente,
            )
            u.password = "Pass1234!"
            db.session.add(u)
            db.session.flush()
            h = Huesped(id_usuario=u.id, documento_id="EXP-CREAR", tipo_documento="cc")
            db.session.add(h)
            hab = Habitacion(
                numero="EXP-CREAR", tipo=TipoHabitacion.simple,
                precio_noche=Decimal("100000"), capacidad=1,
                estado=EstadoHabitacion.disponible,
            )
            db.session.add(hab)
            db.session.commit()

            datos = {
                "id_habitacion": hab.id,
                "fecha_entrada": (date.today() + timedelta(days=5)).isoformat(),
                "fecha_salida": (date.today() + timedelta(days=7)).isoformat(),
            }
            resultado = crear(datos, u)
            assert resultado["expira_en"] is not None
