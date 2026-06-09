"""
Seed demo para desarrollo local.

Puebla 3 usuarios reales de ejemplo y varias relaciones para visualizar mejor
los listados de CRUD: huéspedes, habitaciones, reservas, pagos, servicios,
facturas y puntos.

Uso:
    FLASK_ENV=development python scripts/seed_demo_data.py
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
import os
import secrets
import sys


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models.checkin_checkout import CheckInCheckOut
from app.models.factura import EstadoFactura, Factura
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, MetodoPago, Pago, TipoPago
from app.models.puntos_fidelidad import PuntosFidelidad
from app.models.reserva import EstadoReserva, Reserva
from app.models.servicio_adicional import ServicioAdicional, TipoServicio
from app.models.usuario import RolEnum, Usuario


IVA_RATE = Decimal("0.19")


def _normalize_env(value: Optional[str]) -> str:
    env = (value or "development").strip().lower()
    return env if env in {"development", "testing", "production"} else "development"


def _decimal(value) -> Decimal:
    return Decimal(str(value))


def _upsert_usuario(data: dict) -> Usuario:
    usuario = Usuario.query.filter_by(email=data["email"]).one_or_none()
    if usuario is None:
        usuario = Usuario()
        db.session.add(usuario)

    usuario.nombre = data["nombre"]
    usuario.apellido = data["apellido"]
    usuario.email = data["email"]
    usuario.telefono = data["telefono"]
    usuario.rol = data["rol"]
    usuario.activo = True
    usuario.puntos_fidelizacion = data.get("puntos_fidelizacion", 0)
    usuario.password = data["password"]
    return usuario


def _upsert_huesped(usuario: Usuario, data: dict) -> Huesped:
    huesped = Huesped.query.filter_by(id_usuario=usuario.id).one_or_none()
    if huesped is None:
        huesped = Huesped(id_usuario=usuario.id)
        db.session.add(huesped)

    huesped.documento_id = data["documento_id"]
    huesped.tipo_documento = data.get("tipo_documento", "CC")
    huesped.preferencias = data.get("preferencias")
    return huesped


def _upsert_habitacion(data: dict) -> Habitacion:
    habitacion = Habitacion.query.filter_by(numero=data["numero"]).one_or_none()
    if habitacion is None:
        habitacion = Habitacion(numero=data["numero"])
        db.session.add(habitacion)

    habitacion.tipo = data["tipo"]
    habitacion.descripcion = data["descripcion"]
    habitacion.precio_noche = _decimal(data["precio_noche"])
    habitacion.capacidad = data["capacidad"]
    habitacion.piso = data["piso"]
    habitacion.estado = data["estado"]
    habitacion.activo = True
    return habitacion


def _upsert_reserva(data: dict) -> Reserva:
    reserva = Reserva.query.filter_by(
        id_huesped=data["id_huesped"],
        id_habitacion=data["id_habitacion"],
        fecha_entrada=data["fecha_entrada"],
        fecha_salida=data["fecha_salida"],
    ).one_or_none()
    if reserva is None:
        reserva = Reserva(
            id_huesped=data["id_huesped"],
            id_habitacion=data["id_habitacion"],
            fecha_entrada=data["fecha_entrada"],
            fecha_salida=data["fecha_salida"],
            noches=data["noches"],
            subtotal=data["subtotal"],
            impuestos=data["impuestos"],
            total=data["total"],
        )
        db.session.add(reserva)

    reserva.noches = data["noches"]
    reserva.subtotal = data["subtotal"]
    reserva.impuestos = data["impuestos"]
    reserva.total = data["total"]
    reserva.estado = data["estado"]
    reserva.motivo_cancelacion = data.get("motivo_cancelacion")
    reserva.fecha_reserva = data.get("fecha_reserva", reserva.fecha_reserva)
    return reserva


def _upsert_pago(data: dict) -> Pago:
    pago = Pago.query.filter_by(
        id_reserva=data["id_reserva"],
        tipo=data["tipo"],
    ).one_or_none()
    if pago is None:
        pago = Pago(id_reserva=data["id_reserva"], tipo=data["tipo"])
        db.session.add(pago)

    pago.monto = data["monto"]
    pago.metodo = data["metodo"]
    pago.estado = data["estado"]
    pago.referencia_externa = data.get("referencia_externa")
    return pago


def _upsert_servicio(data: dict) -> ServicioAdicional:
    servicio = ServicioAdicional.query.filter_by(
        id_reserva=data["id_reserva"],
        tipo=data["tipo"],
        descripcion=data["descripcion"],
    ).one_or_none()
    if servicio is None:
        servicio = ServicioAdicional(
            id_reserva=data["id_reserva"],
            tipo=data["tipo"],
            descripcion=data["descripcion"],
            costo=data["costo"],
        )
        db.session.add(servicio)

    servicio.recurso = data.get("recurso")
    servicio.costo = data["costo"]
    servicio.duracion_minutos = data.get("duracion_minutos", 60)
    servicio.fecha_hora = data.get("fecha_hora", servicio.fecha_hora)
    return servicio


def _upsert_factura(data: dict) -> Factura:
    factura = Factura.query.filter_by(id_reserva=data["id_reserva"]).one_or_none()
    if factura is None:
        factura = Factura(id_reserva=data["id_reserva"])
        db.session.add(factura)

    factura.subtotal = data["subtotal"]
    factura.impuestos = data["impuestos"]
    factura.servicios_adicionales_total = data["servicios_adicionales_total"]
    factura.total = data["total"]
    factura.estado = data["estado"]
    factura.pdf_path = data.get("pdf_path")
    factura.fecha_emision = data.get("fecha_emision", factura.fecha_emision)
    return factura


def _upsert_checkin(data: dict) -> CheckInCheckOut:
    registro = CheckInCheckOut.query.filter_by(id_reserva=data["id_reserva"]).one_or_none()
    if registro is None:
        registro = CheckInCheckOut(id_reserva=data["id_reserva"])
        db.session.add(registro)

    registro.fecha_checkin = data.get("fecha_checkin")
    registro.fecha_checkout = data.get("fecha_checkout")
    registro.realizado_por = data.get("realizado_por")
    return registro


def _upsert_puntos(data: dict) -> PuntosFidelidad:
    puntos = PuntosFidelidad.query.filter_by(
        id_huesped=data["id_huesped"],
        id_reserva=data.get("id_reserva"),
        concepto=data["concepto"],
    ).one_or_none()
    if puntos is None:
        puntos = PuntosFidelidad(
            id_huesped=data["id_huesped"],
            id_reserva=data.get("id_reserva"),
            concepto=data["concepto"],
            puntos=data["puntos"],
        )
        db.session.add(puntos)

    puntos.puntos = data["puntos"]
    puntos.fecha = data.get("fecha", puntos.fecha)
    return puntos


def main() -> int:
    env = _normalize_env(os.environ.get("FLASK_ENV"))
    if env == "production":
        print("Seed demo no permitido en producción.")
        return 1

    app = create_app(env)

    with app.app_context():
        db.create_all()

        hoy = date.today()
        ahora = datetime.now()

        admin_pw = secrets.token_urlsafe(12)
        recep_pw = secrets.token_urlsafe(12)
        cliente1_pw = secrets.token_urlsafe(12)
        cliente2_pw = secrets.token_urlsafe(12)

        usuarios = {
            "admin": _upsert_usuario({
                "nombre": "Camila",
                "apellido": "Torres",
                "email": "admin@hotel.com",
                "telefono": "3005550101",
                "rol": RolEnum.admin,
                "password": admin_pw,
            }),
            "recepcionista": _upsert_usuario({
                "nombre": "Andrés",
                "apellido": "López",
                "email": "recepcionista@hotel.com",
                "telefono": "3005550202",
                "rol": RolEnum.recepcionista,
                "password": recep_pw,
            }),
            "cliente": _upsert_usuario({
                "nombre": "Carolina",
                "apellido": "Gómez",
                "email": "carolina.gomez@hotel.com",
                "telefono": "3005550303",
                "rol": RolEnum.cliente,
                "password": cliente1_pw,
                "puntos_fidelizacion": 120,
            }),
            "cliente2": _upsert_usuario({
                "nombre": "Roberto",
                "apellido": "Mendoza",
                "email": "roberto.mendoza@hotel.com",
                "telefono": "3005550404",
                "rol": RolEnum.cliente,
                "password": cliente2_pw,
                "puntos_fidelizacion": 50,
            }),
        }

        db.session.flush()

        huesped = _upsert_huesped(usuarios["cliente"], {
            "documento_id": "CC10293847",
            "tipo_documento": "CC",
            "preferencias": "Habitación silenciosa, cama king y desayuno temprano.",
        })

        huesped2 = _upsert_huesped(usuarios["cliente2"], {
            "documento_id": "CC55887733",
            "tipo_documento": "CC",
            "preferencias": "Cama twin, piso alto, sin mascotas.",
        })

        db.session.flush()

        habitaciones = {
            "101": _upsert_habitacion({
                "numero": "101",
                "tipo": TipoHabitacion.simple,
                "descripcion": "Habitación simple con vista interior.",
                "precio_noche": "180000",
                "capacidad": 1,
                "piso": 1,
                "estado": EstadoHabitacion.disponible,
            }),
            "102": _upsert_habitacion({
                "numero": "102",
                "tipo": TipoHabitacion.simple,
                "descripcion": "Habitación simple con ventana a la calle.",
                "precio_noche": "200000",
                "capacidad": 1,
                "piso": 1,
                "estado": EstadoHabitacion.disponible,
            }),
            "201": _upsert_habitacion({
                "numero": "201",
                "tipo": TipoHabitacion.doble,
                "descripcion": "Habitación doble con dos camas.",
                "precio_noche": "240000",
                "capacidad": 2,
                "piso": 2,
                "estado": EstadoHabitacion.disponible,
            }),
            "202": _upsert_habitacion({
                "numero": "202",
                "tipo": TipoHabitacion.doble,
                "descripcion": "Habitación doble con escritorio de trabajo.",
                "precio_noche": "260000",
                "capacidad": 2,
                "piso": 2,
                "estado": EstadoHabitacion.disponible,
            }),
            "301": _upsert_habitacion({
                "numero": "301",
                "tipo": TipoHabitacion.suite,
                "descripcion": "Suite junior con balcón.",
                "precio_noche": "380000",
                "capacidad": 2,
                "piso": 3,
                "estado": EstadoHabitacion.ocupada,
            }),
            "303": _upsert_habitacion({
                "numero": "303",
                "tipo": TipoHabitacion.suite,
                "descripcion": "Suite ejecutiva con sala pequeña.",
                "precio_noche": "420000",
                "capacidad": 3,
                "piso": 3,
                "estado": EstadoHabitacion.disponible,
            }),
            "404": _upsert_habitacion({
                "numero": "404",
                "tipo": TipoHabitacion.deluxe,
                "descripcion": "Deluxe en mantenimiento para demo de estados.",
                "precio_noche": "550000",
                "capacidad": 2,
                "piso": 4,
                "estado": EstadoHabitacion.mantenimiento,
            }),
            "501": _upsert_habitacion({
                "numero": "501",
                "tipo": TipoHabitacion.deluxe,
                "descripcion": "Suite presidencial con jacuzzi y terraza.",
                "precio_noche": "780000",
                "capacidad": 4,
                "piso": 5,
                "estado": EstadoHabitacion.disponible,
            }),
        }

        db.session.flush()

        reserva_pasada_entrada = hoy - timedelta(days=9)
        reserva_pasada_salida = hoy - timedelta(days=6)
        reserva_pasada_noches = (reserva_pasada_salida - reserva_pasada_entrada).days
        reserva_pasada_subtotal = _decimal(habitaciones["101"].precio_noche) * reserva_pasada_noches
        reserva_pasada_impuestos = (reserva_pasada_subtotal * IVA_RATE).quantize(Decimal("0.01"))
        reserva_pasada_total = reserva_pasada_subtotal + reserva_pasada_impuestos

        reserva_futura_entrada = hoy + timedelta(days=3)
        reserva_futura_salida = hoy + timedelta(days=6)
        reserva_futura_noches = (reserva_futura_salida - reserva_futura_entrada).days
        reserva_futura_subtotal = _decimal(habitaciones["202"].precio_noche) * reserva_futura_noches
        reserva_futura_impuestos = (reserva_futura_subtotal * IVA_RATE).quantize(Decimal("0.01"))
        reserva_futura_total = reserva_futura_subtotal + reserva_futura_impuestos

        reserva_pendiente_entrada = hoy + timedelta(days=12)
        reserva_pendiente_salida = hoy + timedelta(days=14)
        reserva_pendiente_noches = (reserva_pendiente_salida - reserva_pendiente_entrada).days
        reserva_pendiente_subtotal = _decimal(habitaciones["303"].precio_noche) * reserva_pendiente_noches
        reserva_pendiente_impuestos = (reserva_pendiente_subtotal * IVA_RATE).quantize(Decimal("0.01"))
        reserva_pendiente_total = reserva_pendiente_subtotal + reserva_pendiente_impuestos

        reserva_pasada = _upsert_reserva({
            "id_huesped": huesped.id,
            "id_habitacion": habitaciones["101"].id,
            "fecha_entrada": reserva_pasada_entrada,
            "fecha_salida": reserva_pasada_salida,
            "noches": reserva_pasada_noches,
            "subtotal": reserva_pasada_subtotal,
            "impuestos": reserva_pasada_impuestos,
            "total": reserva_pasada_total,
            "estado": EstadoReserva.completada,
            "fecha_reserva": ahora - timedelta(days=10),
        })

        reserva_futura = _upsert_reserva({
            "id_huesped": huesped.id,
            "id_habitacion": habitaciones["202"].id,
            "fecha_entrada": reserva_futura_entrada,
            "fecha_salida": reserva_futura_salida,
            "noches": reserva_futura_noches,
            "subtotal": reserva_futura_subtotal,
            "impuestos": reserva_futura_impuestos,
            "total": reserva_futura_total,
            "estado": EstadoReserva.confirmada,
            "fecha_reserva": ahora - timedelta(days=2),
        })

        reserva_pendiente = _upsert_reserva({
            "id_huesped": huesped.id,
            "id_habitacion": habitaciones["303"].id,
            "fecha_entrada": reserva_pendiente_entrada,
            "fecha_salida": reserva_pendiente_salida,
            "noches": reserva_pendiente_noches,
            "subtotal": reserva_pendiente_subtotal,
            "impuestos": reserva_pendiente_impuestos,
            "total": reserva_pendiente_total,
            "estado": EstadoReserva.pendiente,
            "fecha_reserva": ahora - timedelta(hours=6),
        })

        db.session.flush()

        # Reservas para Roberto (huesped2)
        reserva_roberto_entrada = hoy - timedelta(days=3)
        reserva_roberto_salida = hoy
        reserva_roberto_noches = (reserva_roberto_salida - reserva_roberto_entrada).days
        reserva_roberto_subtotal = _decimal(habitaciones["301"].precio_noche) * reserva_roberto_noches
        reserva_roberto_impuestos = (reserva_roberto_subtotal * IVA_RATE).quantize(Decimal("0.01"))
        reserva_roberto_total = reserva_roberto_subtotal + reserva_roberto_impuestos

        reserva_roberto = _upsert_reserva({
            "id_huesped": huesped2.id,
            "id_habitacion": habitaciones["301"].id,
            "fecha_entrada": reserva_roberto_entrada,
            "fecha_salida": reserva_roberto_salida,
            "noches": reserva_roberto_noches,
            "subtotal": reserva_roberto_subtotal,
            "impuestos": reserva_roberto_impuestos,
            "total": reserva_roberto_total,
            "estado": EstadoReserva.confirmada,
            "fecha_reserva": ahora - timedelta(days=5),
        })

        db.session.flush()

        _upsert_pago({
            "id_reserva": reserva_roberto.id,
            "tipo": TipoPago.garantia,
            "monto": (reserva_roberto_total * Decimal("0.50")).quantize(Decimal("0.01")),
            "metodo": MetodoPago.tarjeta,
            "estado": EstadoPago.aprobado,
            "referencia_externa": "demo-garantia-301",
        })

        _upsert_servicio({
            "id_reserva": reserva_roberto.id,
            "tipo": TipoServicio.comedor,
            "descripcion": "Cena romántica para dos",
            "recurso": "Restaurante principal",
            "costo": _decimal("120000.00"),
            "duracion_minutos": 90,
            "fecha_hora": ahora - timedelta(days=1, hours=8),
        })

        _upsert_checkin({
            "id_reserva": reserva_roberto.id,
            "fecha_checkin": ahora - timedelta(days=2),
            "realizado_por": usuarios["recepcionista"].id,
        })

        _upsert_puntos({
            "id_huesped": huesped2.id,
            "id_reserva": reserva_roberto.id,
            "puntos": reserva_roberto_noches * 10,
            "concepto": "Estadía en curso - demo",
            "fecha": ahora - timedelta(days=2),
        })

        _upsert_pago({
            "id_reserva": reserva_pasada.id,
            "tipo": TipoPago.garantia,
            "monto": (reserva_pasada_total * Decimal("0.50")).quantize(Decimal("0.01")),
            "metodo": MetodoPago.efectivo,
            "estado": EstadoPago.aprobado,
            "referencia_externa": "demo-garantia-101",
        })
        _upsert_pago({
            "id_reserva": reserva_pasada.id,
            "tipo": TipoPago.liquidacion,
            "monto": (reserva_pasada_total + Decimal("135000.00") - (reserva_pasada_total * Decimal("0.50"))).quantize(Decimal("0.01")),
            "metodo": MetodoPago.transferencia,
            "estado": EstadoPago.aprobado,
            "referencia_externa": "demo-liquidacion-101",
        })
        _upsert_pago({
            "id_reserva": reserva_futura.id,
            "tipo": TipoPago.garantia,
            "monto": (reserva_futura_total * Decimal("0.50")).quantize(Decimal("0.01")),
            "metodo": MetodoPago.tarjeta,
            "estado": EstadoPago.aprobado,
            "referencia_externa": "demo-garantia-202",
        })

        _upsert_servicio({
            "id_reserva": reserva_pasada.id,
            "tipo": TipoServicio.comedor,
            "descripcion": "Desayuno ejecutivo para dos personas",
            "recurso": "Restaurante principal",
            "costo": _decimal("75000.00"),
            "duracion_minutos": 45,
            "fecha_hora": ahora - timedelta(days=8, hours=2),
        })
        _upsert_servicio({
            "id_reserva": reserva_pasada.id,
            "tipo": TipoServicio.spa,
            "descripcion": "Masaje relajante de 60 minutos",
            "recurso": "Sala spa 1",
            "costo": _decimal("60000.00"),
            "duracion_minutos": 60,
            "fecha_hora": ahora - timedelta(days=7, hours=5),
        })

        _upsert_checkin({
            "id_reserva": reserva_pasada.id,
            "fecha_checkin": ahora - timedelta(days=8),
            "fecha_checkout": ahora - timedelta(days=6),
            "realizado_por": usuarios["recepcionista"].id,
        })

        _upsert_factura({
            "id_reserva": reserva_pasada.id,
            "subtotal": reserva_pasada_subtotal,
            "impuestos": reserva_pasada_impuestos,
            "servicios_adicionales_total": _decimal("135000.00"),
            "total": (reserva_pasada_total + _decimal("135000.00")).quantize(Decimal("0.01")),
            "estado": EstadoFactura.emitida,
            "pdf_path": "/demo/facturas/factura-reserva-101.pdf",
            "fecha_emision": ahora - timedelta(days=6),
        })

        _upsert_puntos({
            "id_huesped": huesped.id,
            "id_reserva": reserva_pasada.id,
            "puntos": reserva_pasada_noches * 10,
            "concepto": "Estadía completada - demo",
            "fecha": ahora - timedelta(days=6),
        })

        db.session.commit()

        print("Seed demo aplicado correctamente.")
        print("")
        print("Usuarios cargados (contraseñas generadas aleatoriamente):")
        print(f" - admin@hotel.com / {admin_pw}          → Camila Torres (Admin)")
        print(f" - recepcionista@hotel.com / {recep_pw}  → Andrés López (Recepcionista)")
        print(f" - carolina.gomez@hotel.com / {cliente1_pw} → Carolina Gómez (Cliente)")
        print(f" - roberto.mendoza@hotel.com / {cliente2_pw} → Roberto Mendoza (Cliente)")
        print("")
        print("Habitaciones: 8 (101, 102, 201, 202, 301, 303, 404, 501)")
        print("")
        print("Reservas demo:")
        print(f" - Completada: hab 101, id {reserva_pasada.id} (Carolina)")
        print(f" - Confirmada: hab 202, id {reserva_futura.id} (Carolina)")
        print(f" - Pendiente:  hab 303, id {reserva_pendiente.id} (Carolina)")
        print(f" - En curso:   hab 301, id {reserva_roberto.id} (Roberto)")
        return 0


if __name__ == "__main__":
    sys.exit(main())