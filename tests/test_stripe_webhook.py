import pytest
from unittest.mock import patch
from decimal import Decimal
from datetime import date, timedelta

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app.models.reserva import EstadoReserva, Reserva
from app.models.usuario import RolEnum, Usuario
from app.services.stripe_webhook_service import (
    procesar_evento,
    _buscar_por_payment_intent,
    _manejar_payment_failed,
    _manejar_payment_succeeded,
    _manejar_charge_refunded,
)


def _crear_pago_con_reserva(seed: str, estado_pago=EstadoPago.pendiente):
    u = Usuario(
        nombre="Cli", apellido="WH",
        email=f"wh_{seed}@test.com", rol=RolEnum.cliente,
    )
    u.password = "Pass1234!"
    db.session.add(u)
    db.session.flush()
    h = Huesped(id_usuario=u.id, documento_id=f"WH-{seed}", tipo_documento="cc")
    db.session.add(h)
    hab = Habitacion(
        numero=f"WH-{seed}", tipo=TipoHabitacion.simple,
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
        estado=EstadoReserva.pendiente,
    )
    db.session.add(r)
    db.session.flush()
    pago = Pago(
        id_reserva=r.id, monto=Decimal("119000"),
        metodo=MetodoPago.tarjeta, tipo=TipoPago.garantia,
        estado=estado_pago, stripe_payment_intent_id=f"pi_{seed}",
    )
    db.session.add(pago)
    db.session.commit()
    return pago, r


SECRET = "whsec_test_secret"


class TestProcesarEvento:
    def test_sin_secret_retorna_error(self, app):
        with app.app_context():
            resultado = procesar_evento(b"{}", "test_sig")
            assert resultado["procesado"] is False
            assert "WEBHOOK_SECRET no configurado" in resultado["detalle"]

    @patch("app.services.stripe_webhook_service.stripe.Webhook.construct_event")
    def test_payload_invalido(self, mock_construct, app):
        mock_construct.side_effect = ValueError("Invalid payload")
        with app.app_context():
            app.config["STRIPE_WEBHOOK_SECRET"] = SECRET
            resultado = procesar_evento(b"{}", "test_sig")
            assert resultado["procesado"] is False
            assert "Payload inválido" in resultado["detalle"]

    @patch("app.services.stripe_webhook_service.stripe.Webhook.construct_event")
    def test_firma_invalida(self, mock_construct, app):
        from stripe import SignatureVerificationError as SVE
        mock_construct.side_effect = SVE("Bad sig", "{}", "sig")
        with app.app_context():
            app.config["STRIPE_WEBHOOK_SECRET"] = SECRET
            resultado = procesar_evento(b"{}", "test_sig")
            assert resultado["procesado"] is False
            assert "Firma del webhook inválida" in resultado["detalle"]

    @patch("app.services.stripe_webhook_service.stripe.Webhook.construct_event")
    def test_tipo_no_manejado(self, mock_construct, app):
        mock_construct.return_value = {"type": "charge.succeeded", "data": {"object": {}}}
        with app.app_context():
            app.config["STRIPE_WEBHOOK_SECRET"] = SECRET
            resultado = procesar_evento(b"{}", "test_sig")
            assert resultado["procesado"] is False
            assert "Evento no manejado" in resultado["detalle"]

    @patch("app.services.stripe_webhook_service.stripe.Webhook.construct_event")
    def test_payment_succeeded_procesa(self, mock_construct, app):
        mock_construct.return_value = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_ev_succ"}},
        }
        with app.app_context():
            app.config["STRIPE_WEBHOOK_SECRET"] = SECRET
            _crear_pago_con_reserva("ev_succ")
            resultado = procesar_evento(b"{}", "test_sig")
            assert resultado["procesado"] is True

    @patch("app.services.stripe_webhook_service.stripe.Webhook.construct_event")
    def test_payment_failed_procesa(self, mock_construct, app):
        mock_construct.return_value = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_ev_fail",
                    "last_payment_error": {"message": "Fondos insuficientes"},
                }
            },
        }
        with app.app_context():
            app.config["STRIPE_WEBHOOK_SECRET"] = SECRET
            _crear_pago_con_reserva("ev_fail")
            resultado = procesar_evento(b"{}", "test_sig")
            assert resultado["procesado"] is True

    @patch("app.services.stripe_webhook_service.stripe.Webhook.construct_event")
    def test_charge_refunded_procesa(self, mock_construct, app):
        mock_construct.return_value = {
            "type": "charge.refunded",
            "data": {
                "object": {
                    "payment_intent": "pi_ev_ref",
                    "amount_refunded": 11900000,
                }
            },
        }
        with app.app_context():
            app.config["STRIPE_WEBHOOK_SECRET"] = SECRET
            _crear_pago_con_reserva("ev_ref")
            resultado = procesar_evento(b"{}", "test_sig")
            assert resultado["procesado"] is True

    @patch("app.services.stripe_webhook_service.stripe.Webhook.construct_event")
    def test_handler_excepcion_hace_rollback(self, mock_construct, app):
        mock_construct.return_value = {
            "type": "payment_intent.succeeded",
            "data": {"object": {}},
        }
        with app.app_context():
            app.config["STRIPE_WEBHOOK_SECRET"] = SECRET
            resultado = procesar_evento(b"{}", "test_sig")
            assert resultado["procesado"] is False


class TestWebhookEndpoint:
    def test_sin_firma_retorna_400(self, client, app):
        resp = client.post(
            "/api/v1/pagos/webhook",
            data=b"{}",
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["procesado"] is False


class TestBuscarPaymentIntent:
    def test_sin_resultado_retorna_none(self, app):
        with app.app_context():
            resultado = _buscar_por_payment_intent("pi_no_existe")
            assert resultado is None


class TestManejadoresUnitarios:
    def test_payment_failed_sin_pago(self, app):
        with app.app_context():
            r = _manejar_payment_failed({"id": "pi_x", "last_payment_error": {"message": "err"}})
            assert "no asociado" in r

    def test_payment_succeeded_sin_pago(self, app):
        with app.app_context():
            r = _manejar_payment_succeeded({"id": "pi_x"})
            assert "no asociado" in r

    def test_payment_succeeded_ya_aprobado(self, app):
        with app.app_context():
            _crear_pago_con_reserva("man_aprob", EstadoPago.aprobado)
            r = _manejar_payment_succeeded({"id": "pi_man_aprob"})
            assert "ya estaba aprobado" in r

    def test_charge_refunded_sin_payment_intent(self, app):
        with app.app_context():
            r = _manejar_charge_refunded({"amount_refunded": 1000})
            assert "sin payment_intent" in r

    def test_charge_refunded_sin_pago(self, app):
        with app.app_context():
            r = _manejar_charge_refunded({"payment_intent": "pi_x", "amount_refunded": 1000})
            assert "no asociado" in r

    def test_charge_refunded_sin_monto(self, app):
        with app.app_context():
            _crear_pago_con_reserva("ref_nomonto", EstadoPago.aprobado)
            r = _manejar_charge_refunded({"payment_intent": "pi_ref_nomonto", "amount_refunded": 0})
            assert "sin monto" in r

    def test_payment_succeeded_confirma_reserva_pendiente(self, app):
        with app.app_context():
            pago, reserva = _crear_pago_con_reserva("conf_res")
            r = _manejar_payment_succeeded({"id": "pi_conf_res"})
            db.session.commit()
            assert "confirmado" in r
            db.session.refresh(reserva)
            assert reserva.estado == EstadoReserva.confirmada

    def test_charge_refunded_crea_reembolso(self, app):
        with app.app_context():
            pago, _ = _crear_pago_con_reserva("crea_reemb", EstadoPago.aprobado)
            r = _manejar_charge_refunded({"payment_intent": "pi_crea_reemb", "amount_refunded": 11900000})
            assert "reembolsado" in r
            db.session.refresh(pago)
            assert pago.estado == EstadoPago.reembolsado
            assert pago.reembolso is not None
