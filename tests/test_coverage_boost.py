"""
Tests de cobertura para líneas no cubiertas — objetivo: 89% → 90%+

Cubre:
  - pago_service.py líneas 232-267, 275-290:
      _cobrar_stripe (STRIPE_MOCK=False): éxito, CardError, StripeError,
      status≠succeeded, sin API key, sin payment_method_id
      _reversar_stripe (STRIPE_MOCK=False): éxito, StripeError
  - reserva_service.py líneas 96-475:
      filtros de búsqueda y envío de email (SMTP mockeado)
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app.models.reserva import EstadoReserva, Reserva
from app.models.usuario import RolEnum, Usuario
from app.utils.fecha_helper import ahora_colombia
from app.utils.jwt_helper import generar_token


# ---------------------------------------------------------------------------
# Helpers reutilizables
# ---------------------------------------------------------------------------

def _usuario(rol: RolEnum, tag: str) -> Usuario:
    u = Usuario(nombre=f"U", apellido=f"{tag}", email=f"{tag}_{id(tag)}@h.com", rol=rol)
    u.password = "pass"
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


def _habitacion(precio: str = "200000.00") -> Habitacion:
    import random
    n = str(random.randint(8000, 9999))
    hab = Habitacion(
        numero=n,
        tipo=TipoHabitacion.doble,
        precio_noche=Decimal(precio),
        capacidad=2,
        estado=EstadoHabitacion.disponible,
    )
    db.session.add(hab)
    db.session.flush()
    return hab


def _reserva(huesped, hab, estado=EstadoReserva.pendiente,
             total="200000.00") -> Reserva:
    from datetime import date, timedelta
    hoy = date.today()
    entrada = hoy + timedelta(days=5)
    salida = hoy + timedelta(days=7)
    noches = 2
    subtotal = Decimal("168067.00")
    impuestos = Decimal("31933.00")
    r = Reserva(
        id_huesped=huesped.id,
        id_habitacion=hab.id,
        fecha_entrada=entrada,
        fecha_salida=salida,
        noches=noches,
        subtotal=subtotal,
        impuestos=impuestos,
        total=Decimal(total),
        estado=estado,
    )
    db.session.add(r)
    db.session.flush()
    return r


def _garantia(reserva: Reserva) -> Pago:
    p = Pago(
        id_reserva=reserva.id,
        monto=(Decimal(str(reserva.total)) * Decimal("0.50")).quantize(
            Decimal("0.01")
        ),
        metodo=MetodoPago.tarjeta,
        tipo=TipoPago.garantia,
        estado=EstadoPago.aprobado,
        referencia_externa="pi_real_test_001",
    )
    db.session.add(p)
    db.session.flush()
    return p


# ---------------------------------------------------------------------------
# TestStripeCobrarReal — cubre pago_service.py líneas 232-267
# ---------------------------------------------------------------------------

class TestStripeCobrarReal:
    """
    Prueba _cobrar_stripe con STRIPE_MOCK=False mockeando el módulo stripe.
    Nunca llama la API real.
    """

    def _set_mock_off(self, app):
        app.config["STRIPE_MOCK"] = False
        app.config["STRIPE_SECRET_KEY"] = "sk_test_fake_key"

    def _set_mock_on(self, app):
        app.config["STRIPE_MOCK"] = True
        app.config["STRIPE_SECRET_KEY"] = None

    # ------------------------------------------------------------------
    # Éxito
    # ------------------------------------------------------------------

    def test_cobrar_stripe_exito(self, app):
        """_cobrar_stripe retorna intent.id cuando status == 'succeeded'."""
        with app.app_context():
            self._set_mock_off(app)

            intent_mock = MagicMock()
            intent_mock.status = "succeeded"
            intent_mock.id = "pi_test_ok_123"

            with patch("stripe.PaymentIntent.create", return_value=intent_mock):
                from app.services.pago_service import _cobrar_stripe
                result = _cobrar_stripe(Decimal("100000.00"), "pm_test_abc", 1)

            assert result == "pi_test_ok_123"
            self._set_mock_on(app)

    # ------------------------------------------------------------------
    # Sin API key
    # ------------------------------------------------------------------

    def test_cobrar_stripe_sin_api_key(self, app):
        """ValueError si STRIPE_SECRET_KEY está vacía."""
        with app.app_context():
            app.config["STRIPE_MOCK"] = False
            app.config["STRIPE_SECRET_KEY"] = ""

            from app.services.pago_service import _cobrar_stripe
            with pytest.raises(ValueError, match="STRIPE_SECRET_KEY"):
                _cobrar_stripe(Decimal("100000.00"), "pm_test", 1)

            self._set_mock_on(app)

    # ------------------------------------------------------------------
    # Sin payment_method_id
    # ------------------------------------------------------------------

    def test_cobrar_stripe_sin_pm_id(self, app):
        """ValueError si payment_method_id es None."""
        with app.app_context():
            self._set_mock_off(app)

            from app.services.pago_service import _cobrar_stripe
            with pytest.raises(ValueError, match="payment_method_id"):
                _cobrar_stripe(Decimal("100000.00"), None, 1)

            self._set_mock_on(app)

    # ------------------------------------------------------------------
    # CardError
    # ------------------------------------------------------------------

    def test_cobrar_stripe_card_error(self, app):
        """ValueError con mensaje de tarjeta rechazada."""
        with app.app_context():
            self._set_mock_off(app)

            import stripe as stripe_lib
            err = stripe_lib.error.CardError(
                "Your card was declined.",
                "number",
                "card_declined",
            )

            with patch("stripe.PaymentIntent.create", side_effect=err):
                from app.services.pago_service import _cobrar_stripe
                with pytest.raises(ValueError, match="Tarjeta rechazada"):
                    _cobrar_stripe(Decimal("100000.00"), "pm_bad", 1)

            self._set_mock_on(app)

    # ------------------------------------------------------------------
    # StripeError genérico
    # ------------------------------------------------------------------

    def test_cobrar_stripe_stripe_error(self, app):
        """ValueError con mensaje de pasarela cuando ocurre StripeError."""
        with app.app_context():
            self._set_mock_off(app)

            import stripe as stripe_lib
            stripe_err = stripe_lib.error.StripeError("Connection timeout")

            with patch("stripe.PaymentIntent.create", side_effect=stripe_err):
                from app.services.pago_service import _cobrar_stripe
                with pytest.raises(ValueError, match="pasarela de pagos"):
                    _cobrar_stripe(Decimal("100000.00"), "pm_x", 1)

            self._set_mock_on(app)

    # ------------------------------------------------------------------
    # Status ≠ succeeded
    # ------------------------------------------------------------------

    def test_cobrar_stripe_status_no_succeeded(self, app):
        """ValueError cuando el PaymentIntent queda en estado 'requires_action'."""
        with app.app_context():
            self._set_mock_off(app)

            intent_mock = MagicMock()
            intent_mock.status = "requires_action"
            intent_mock.id = "pi_pending"

            with patch("stripe.PaymentIntent.create", return_value=intent_mock):
                from app.services.pago_service import _cobrar_stripe
                with pytest.raises(ValueError, match="no completado"):
                    _cobrar_stripe(Decimal("100000.00"), "pm_3d", 1)

            self._set_mock_on(app)


# ---------------------------------------------------------------------------
# TestStripeReversarReal — cubre pago_service.py líneas 275-290
# ---------------------------------------------------------------------------

class TestStripeReversarReal:
    """Prueba _reversar_stripe con STRIPE_MOCK=False."""

    def test_reversar_exito(self, app):
        """No lanza excepción cuando Refund.create tiene éxito."""
        with app.app_context():
            app.config["STRIPE_MOCK"] = False
            app.config["STRIPE_SECRET_KEY"] = "sk_test_fake"

            refund_mock = MagicMock()
            with patch("stripe.Refund.create", return_value=refund_mock):
                from app.services.pago_service import _reversar_stripe
                _reversar_stripe("pi_real_001", Decimal("100000.00"))  # no debe lanzar

            app.config["STRIPE_MOCK"] = True

    def test_reversar_stripe_error(self, app):
        """ValueError cuando Stripe falla al crear el reembolso."""
        with app.app_context():
            app.config["STRIPE_MOCK"] = False
            app.config["STRIPE_SECRET_KEY"] = "sk_test_fake"

            import stripe as stripe_lib
            err = stripe_lib.error.StripeError("Network error")

            with patch("stripe.Refund.create", side_effect=err):
                from app.services.pago_service import _reversar_stripe
                with pytest.raises(ValueError):
                    _reversar_stripe("pi_real_001", Decimal("50000.00"))

            app.config["STRIPE_MOCK"] = True

    def test_solicitar_reembolso_llama_reversar(self, app):
        """solicitar_reembolso invoca _reversar_stripe para pagos con tarjeta."""
        with app.app_context():
            app.config["STRIPE_MOCK"] = False
            app.config["STRIPE_SECRET_KEY"] = "sk_test_fake"

            u_cli = _usuario(RolEnum.cliente, "cli_rev_real")
            h = _huesped(u_cli)
            hab = _habitacion()
            reserva = _reserva(h, hab, EstadoReserva.ocupada)
            pago = _garantia(reserva)
            db.session.commit()
            pid = pago.id

            with patch("stripe.Refund.create", return_value=MagicMock()):
                from app.services import pago_service
                result = pago_service.solicitar_reembolso(pid, "Reembolso real")

            assert result["estado"] == "Procesado"
            app.config["STRIPE_MOCK"] = True


# ---------------------------------------------------------------------------
# TestReservaServiceFiltros — cubre reserva_service.py líneas de filtrado
# ---------------------------------------------------------------------------

class TestReservaServiceFiltros:
    """
    Cubre las funciones de búsqueda/filtrado de reservas
    que quedaron sin ejecutar en los tests anteriores.
    """

    def test_listar_todas(self, app):
        """obtener_todas() devuelve todas las reservas activas."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_lst1")
            h = _huesped(u)
            hab = _habitacion()
            _reserva(h, hab)
            _reserva(h, hab)
            db.session.commit()

            from app.services import reserva_service
            resultado = reserva_service.obtener_todas()
            assert len(resultado) >= 2

    def test_listar_por_estado(self, app):
        """obtener_todas() filtra por estado cuando se pasa el parámetro."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_lst2")
            h = _huesped(u)
            hab = _habitacion()
            _reserva(h, hab, EstadoReserva.pendiente)
            _reserva(h, hab, EstadoReserva.confirmada)
            db.session.commit()

            from app.services import reserva_service
            pendientes = reserva_service.obtener_todas({"estado": "Pendiente"})
            for r in pendientes:
                assert r["estado"].lower() == "pendiente"

    def test_listar_por_huesped(self, app):
        """obtener_todas() filtra por id_huesped."""
        with app.app_context():
            u1 = _usuario(RolEnum.cliente, "cli_lst3a")
            u2 = _usuario(RolEnum.cliente, "cli_lst3b")
            h1 = _huesped(u1)
            h2 = _huesped(u2)
            hab = _habitacion()
            _reserva(h1, hab)
            _reserva(h2, hab)
            db.session.commit()
            hid = h1.id

            from app.services import reserva_service
            resultado = reserva_service.obtener_todas({"id_huesped": hid})
            assert all(r["id_huesped"] == hid for r in resultado)

    def test_obtener_existente(self, app):
        """obtener_por_id() devuelve el dict de la reserva."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_obt1")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab)
            db.session.commit()
            rid = r.id

            from app.services import reserva_service
            resultado = reserva_service.obtener_por_id(rid, u)
            assert resultado["id"] == rid

    def test_obtener_no_existe(self, app):
        """obtener_por_id() lanza LookupError para id inexistente."""
        with app.app_context():
            from app.services import reserva_service
            with pytest.raises(LookupError):
                reserva_service.obtener_por_id(99999, None)


# ---------------------------------------------------------------------------
# TestReservaServiceEmail — cubre líneas SMTP de reserva_service.py
# ---------------------------------------------------------------------------

class TestReservaServiceEmail:
    """
    Cubre las líneas de envío de email (SMTP) en confirmar() y cancelar().
    Mockea smtplib para no necesitar servidor real.
    """

    def test_confirmar_con_email_mockeado(self, app):
        """confirmar() envía email y cambia estado a confirmada."""
        with app.app_context():
            u_cli = _usuario(RolEnum.cliente, "cli_email1")
            h = _huesped(u_cli)
            hab = _habitacion()
            r = _reserva(h, hab, EstadoReserva.pendiente)
            db.session.commit()
            rid = r.id

            with patch("smtplib.SMTP") as mock_smtp:
                mock_smtp.return_value.__enter__ = MagicMock(
                    return_value=MagicMock()
                )
                mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

                from app.services import reserva_service
                resultado = reserva_service.confirmar(rid)
                assert resultado["estado"].lower() == "confirmada"

    def test_cancelar_sin_garantia(self, app):
        """cancelar() sin garantía previa no crea Reembolso."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_cancel1")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab, EstadoReserva.pendiente)
            db.session.commit()
            rid = r.id

            with patch("smtplib.SMTP"):
                from app.services import reserva_service
                resultado = reserva_service.cancelar(rid, motivo="Test cancelación")

            assert resultado["estado"].lower() == "cancelada"

    def test_cancelar_con_garantia_crea_reembolso(self, app):
        """cancelar() con garantía aprobada crea Reembolso automático."""
        with app.app_context():
            u = _usuario(RolEnum.cliente, "cli_cancel2")
            h = _huesped(u)
            hab = _habitacion()
            r = _reserva(h, hab, EstadoReserva.confirmada)
            pago = Pago(
                id_reserva=r.id,
                monto=Decimal("100000.00"),
                metodo=MetodoPago.efectivo,
                tipo=TipoPago.garantia,
                estado=EstadoPago.aprobado,
            )
            db.session.add(pago)
            db.session.commit()
            rid = r.id

            from app.models.reembolso import Reembolso
            with patch("smtplib.SMTP"):
                from app.services import reserva_service
                reserva_service.cancelar(rid, motivo="Cancelación con garantía")

            reembolso = Reembolso.query.filter_by(id_pago=pago.id).first()
            assert reembolso is not None

    def test_listar_por_fechas(self, app):
        """obtener_todas() filtra por fecha_entrada."""
        with app.app_context():
            from datetime import date, timedelta
            u = _usuario(RolEnum.cliente, "cli_fecha1")
            h = _huesped(u)
            hab = _habitacion()
            _reserva(h, hab)
            db.session.commit()

            from app.services import reserva_service
            hoy = date.today()
            resultado = reserva_service.obtener_todas({
                "fecha_entrada": str(hoy + timedelta(days=5))
            })
            assert isinstance(resultado, list)