"""
Factura Service - Lógica de negocio para facturación (RF-06)
Gestión de facturas: emisión, descarga y anulación.
"""

import os
from decimal import Decimal

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select

from app import db
from app.models.factura import EstadoFactura, Factura
from app.models.reserva import Reserva
from app.models.servicio_adicional import ServicioAdicional
from app.utils.fecha_helper import ahora_colombia


def _get_factura_por_reserva(reserva_id: int) -> Factura:
    factura = db.session.execute(
        select(Factura).filter_by(id_reserva=reserva_id)
    ).scalar_one_or_none()
    if not factura:
        raise LookupError(f"No se encontró factura para la reserva {reserva_id}.")
    return factura


def obtener_por_reserva(reserva_id: int) -> dict:
    """Obtiene la factura asociada a una reserva."""
    factura = _get_factura_por_reserva(reserva_id)
    return factura.to_dict()


def obtener_por_id(factura_id: int) -> dict:
    """Obtiene una factura por su ID."""
    factura = db.session.get(Factura, factura_id)
    if not factura:
        raise LookupError(f"Factura con ID {factura_id} no encontrada.")
    return factura.to_dict()


def listar(filtros=None):
    """Lista todas las facturas con filtros opcionales."""
    query = Factura.query

    if filtros:
        if filtros.get("estado"):
            try:
                estado = EstadoFactura(filtros["estado"])
                query = query.filter_by(estado=estado)
            except ValueError:
                raise ValueError(
                    f"Estado inválido. Valores permitidos: "
                    f"{[e.value for e in EstadoFactura]}"
                )

        if filtros.get("id_reserva"):
            query = query.filter_by(id_reserva=int(filtros["id_reserva"]))

        if filtros.get("fecha_desde"):
            from datetime import date

            fecha = date.fromisoformat(filtros["fecha_desde"])
            query = query.filter(Factura.fecha_emision >= fecha)

        if filtros.get("fecha_hasta"):
            from datetime import date

            fecha = date.fromisoformat(filtros["fecha_hasta"])
            query = query.filter(Factura.fecha_emision <= fecha)

    facturas = query.order_by(Factura.fecha_emision.desc()).all()
    return [f.to_dict() for f in facturas]


def _generar_pdf_factura(factura: Factura) -> str:
    """Genera el PDF de la factura y retorna la ruta del archivo."""
    static_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "static",
        "facturas",
    )
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    pdf_path = os.path.join(static_dir, f"{factura.id_reserva}.pdf")

    reserva = factura.reserva
    huesped = reserva.huesped
    habitacion = reserva.habitacion

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Heading1"],
            alignment=1,
            fontSize=16,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubtitleCenter",
            parent=styles["Normal"],
            alignment=1,
            fontSize=10,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=4,
        )
    )

    elements = []

    elements.append(Paragraph("HOTELBOOK PRO", styles["TitleCenter"]))
    elements.append(
        Paragraph("Av. Principal 123, Pereira, Colombia", styles["SubtitleCenter"])
    )
    elements.append(
        Paragraph("NIT: 123456789-0 | Tel: (606) 1234567", styles["SubtitleCenter"])
    )
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("FACTURA DE ALOJAMIENTO", styles["TitleCenter"]))
    elements.append(Spacer(1, 3 * mm))

    datos_factura = [
        [
            "Factura N°:",
            str(factura.id).zfill(8),
            "Fecha de Emisión:",
            factura.fecha_emision.strftime("%Y-%m-%d"),
        ],
        [
            "Reserva N°:",
            str(factura.id_reserva).zfill(6),
            "Estado:",
            factura.estado.value,
        ],
    ]
    t_datos = Table(datos_factura, colWidths=[40 * mm, 45 * mm, 40 * mm, 45 * mm])
    t_datos.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t_datos)
    elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", styles["SectionHeader"]))
    nombre_cliente = (
        f"{huesped.usuario.nombre} {huesped.usuario.apellido}"
        if huesped and huesped.usuario
        else "No disponible"
    )
    documento = huesped.documento_id if huesped else "No disponible"
    tipo_doc = huesped.tipo_documento if huesped else "CC"
    datos_cliente = [
        ["Nombre:", nombre_cliente, "Documento:", f"{tipo_doc} {documento}"],
        [
            "Email:",
            huesped.usuario.email if huesped and huesped.usuario else "No disponible",
            "",
            "",
        ],
    ]
    t_cliente = Table(datos_cliente, colWidths=[35 * mm, 70 * mm, 35 * mm, 30 * mm])
    t_cliente.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("SPAN", (1, 1), (3, 1)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t_cliente)
    elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph("DETALLE DE LA ESTANCIA", styles["SectionHeader"]))
    datos_estancia = [
        ["Habitación:", f"N° {habitacion.numero}", "Tipo:", habitacion.tipo.value],
        [
            "Entrada:",
            reserva.fecha_entrada.strftime("%Y-%m-%d"),
            "Salida:",
            reserva.fecha_salida.strftime("%Y-%m-%d"),
        ],
        [
            "Noches:",
            str(reserva.noches),
            "Precio/Noche:",
            f"${float(habitacion.precio_noche):.2f}",
        ],
    ]
    t_estancia = Table(datos_estancia, colWidths=[35 * mm, 70 * mm, 35 * mm, 30 * mm])
    t_estancia.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t_estancia)
    elements.append(Spacer(1, 8 * mm))

    servicios = (
        db.session.execute(select(ServicioAdicional).filter_by(id_reserva=reserva.id))
        .scalars()
        .all()
    )
    data_resumen = [["CONCEPTO", "DETALLE", "VALOR"]]
    data_resumen.append(
        [
            "Hospedaje (Subtotal)",
            f"{reserva.noches} noches",
            f"${float(reserva.subtotal):.2f}",
        ]
    )
    data_resumen.append(
        ["IVA 19%", "Impuesto aplicado", f"${float(reserva.impuestos):.2f}"]
    )

    if servicios:
        data_resumen.append(["", "", ""])
        data_resumen.append(["SERVICIOS ADICIONALES", "", ""])
        for s in servicios:
            data_resumen.append(
                [f"  {s.tipo.value}", s.descripcion, f"${float(s.costo):.2f}"]
            )

    total_general = (
        float(reserva.subtotal)
        + float(reserva.impuestos)
        + float(factura.servicios_adicionales_total)
    )
    data_resumen.append(["", "", ""])
    data_resumen.append(["TOTAL A PAGAR", "", f"${total_general:.2f}"])

    col_widths = [60 * mm, 80 * mm, 30 * mm]
    t_resumen = Table(data_resumen, colWidths=col_widths)
    t_resumen.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8E8E8")),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(t_resumen)
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph("ESTADO DE PAGO", styles["SectionHeader"]))
    estado_texto = f"PENDIENTE DE PAGO - Total: ${total_general:.2f}"
    if factura.estado.value == "Pagada":
        estado_texto = f"PAGADA - Total cancelado: ${total_general:.2f}"
    elif factura.estado.value == "Emitida":
        estado_texto = f"EMITIDA - Pendiente de pago: ${total_general:.2f}"
    elif factura.estado.value == "Anulada":
        estado_texto = "ANULADA"
    elements.append(Paragraph(estado_texto, styles["Normal"]))
    elements.append(Spacer(1, 8 * mm))

    elements.append(
        Paragraph(
            "Gracias por su estancia en HotelBook Pro. "
            "Para consultas, comuníquese al (606) 1234567 o hotelbook@example.com",
            styles["Normal"],
        )
    )

    doc.build(elements)
    return pdf_path


def emitir(reserva_id: int) -> dict:
    """
    Emite (o re-emite) una factura para una reserva.
    Recalcula totales, genera PDF y cambia estado a 'emitida'.
    Si ya existe y está emitida, la actualiza (re-emisión).
    """
    factura = _get_factura_por_reserva(reserva_id)

    if factura.estado == EstadoFactura.pagada:
        raise ValueError("No se puede reemitir una factura ya pagada.")
    if factura.estado == EstadoFactura.anulada:
        raise ValueError("No se puede reemitir una factura anulada.")

    servicios = (
        db.session.execute(select(ServicioAdicional).filter_by(id_reserva=reserva_id))
        .scalars()
        .all()
    )
    servicios_total = Decimal("0.00")
    for s in servicios:
        servicios_total += Decimal(str(s.costo))

    reserva = db.session.get(Reserva, reserva_id)
    subtotal_base = Decimal(str(reserva.subtotal))
    impuestos = subtotal_base * Decimal(str(current_app.config["IVA_RATE"]))
    total = subtotal_base + impuestos + servicios_total

    factura.subtotal = reserva.subtotal
    factura.impuestos = round(impuestos, 2)
    factura.servicios_adicionales_total = servicios_total
    factura.total = total
    factura.estado = EstadoFactura.emitida
    factura.fecha_emision = ahora_colombia()

    pdf_path = _generar_pdf_factura(factura)
    factura.pdf_path = pdf_path

    db.session.commit()
    return factura.to_dict()


def descargar(reserva_id: int) -> str:
    """
    Descarga el PDF de una factura.
    Retorna la ruta del archivo para el controlador.
    """
    factura = _get_factura_por_reserva(reserva_id)

    if not factura.pdf_path:
        raise ValueError(
            "La factura no tiene un archivo PDF asociado. " "Debe ser emitida primero."
        )

    if not os.path.exists(factura.pdf_path):
        raise FileNotFoundError(
            f"El archivo PDF '{factura.pdf_path}' no fue encontrado en el servidor."
        )

    return factura.pdf_path


def anular(factura_id: int, motivo: str) -> dict:
    """
    Anula una factura emitida (no pagada).
    No permite anular facturas ya pagadas.
    """
    factura = db.session.get(Factura, factura_id)
    if not factura:
        raise LookupError(f"Factura con ID {factura_id} no encontrada.")

    if factura.estado == EstadoFactura.pagada:
        raise ValueError(
            "No se puede anular una factura que ya fue pagada. "
            "Contacte al administrador."
        )

    if factura.estado == EstadoFactura.anulada:
        raise ValueError("La factura ya está anulada.")

    factura.estado = EstadoFactura.anulada
    db.session.commit()

    resultado = factura.to_dict()
    resultado["motivo_anulacion"] = motivo
    return resultado
