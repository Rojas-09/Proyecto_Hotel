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
    """Genera el PDF de la factura con diseño profesional open-source."""
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

    # ── Colores corporativos ──
    GOLD = "#C8A45C"
    DARK = "#1E2A3A"
    MID = "#2C3E50"
    LIGHT = "#F5F5F0"
    WHITE = colors.white
    BLACK = colors.HexColor("#333333")
    GRAY = colors.HexColor("#888888")
    LIGHT_GRAY = colors.HexColor("#E8E8E3")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    # ── Estilos personalizados ──
    styles.add(ParagraphStyle(
        name="BrandHeader", fontName="Helvetica-Bold", fontSize=22,
        textColor=colors.HexColor(DARK), spaceAfter=2, alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="BrandSub", fontName="Helvetica", fontSize=8,
        textColor=GRAY, spaceAfter=0, alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="InvoiceTitle", fontName="Helvetica-Bold", fontSize=14,
        textColor=colors.HexColor(GOLD), spaceBefore=4, spaceAfter=2, alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="SectionH", fontName="Helvetica-Bold", fontSize=9,
        textColor=colors.HexColor(MID), spaceBefore=10, spaceAfter=4,
        borderPadding=(0, 0, 2, 0),
    ))
    styles.add(ParagraphStyle(
        name="CellLabel", fontName="Helvetica-Bold", fontSize=8,
        textColor=colors.HexColor(MID),
    ))
    styles.add(ParagraphStyle(
        name="CellValue", fontName="Helvetica", fontSize=8,
        textColor=BLACK,
    ))
    styles.add(ParagraphStyle(
        name="FooterText", fontName="Helvetica", fontSize=7.5,
        textColor=GRAY, alignment=1, spaceBefore=4,
    ))

    elements = []

    # ── ENCABEZADO: Logo + Empresa ──
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "static",
        "logo.png",
    )
    if os.path.exists(logo_path):
        from reportlab.platypus import Image
        logo = Image(logo_path, width=45 * mm, height=15 * mm)
        elements.append(logo)
        elements.append(Spacer(1, 2 * mm))

    header_data = [
        [Paragraph("HOTELBOOK PRO", styles["BrandHeader"]), "", ""],
        [Paragraph("NIT: 123.456.789-0", styles["BrandSub"]),
         Paragraph("Av. Principal 123, Pereira", styles["BrandSub"]),
         Paragraph("Tel: (606) 123 4567", styles["BrandSub"])],
    ]
    t_header = Table(header_data, colWidths=[58 * mm, 58 * mm, 58 * mm])
    t_header.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    elements.append(t_header)

    # ── Línea decorativa ──
    line_data = [["", "", ""]]
    t_line = Table(line_data, colWidths=[58 * mm, 58 * mm, 58 * mm])
    t_line.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1.5, colors.HexColor(GOLD)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_line)
    elements.append(Spacer(1, 3 * mm))

    # ── Título ──
    elements.append(Paragraph("FACTURA DE ALOJAMIENTO", styles["InvoiceTitle"]))
    elements.append(Spacer(1, 4 * mm))

    # ── INFO FACTURA ──
    info_data = [
        [Paragraph("Factura N°", styles["CellLabel"]),
         Paragraph(str(factura.id).zfill(8), styles["CellValue"]),
         Paragraph("Reserva N°", styles["CellLabel"]),
         Paragraph(str(factura.id_reserva).zfill(6), styles["CellValue"])],
        [Paragraph("Fecha Emisión", styles["CellLabel"]),
         Paragraph(factura.fecha_emision.strftime("%Y-%m-%d"), styles["CellValue"]),
         Paragraph("Estado", styles["CellLabel"]),
         Paragraph(factura.estado.value, styles["CellValue"])],
    ]
    t_info = Table(info_data, colWidths=[28 * mm, 45 * mm, 28 * mm, 45 * mm])
    t_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GRAY),
        ("BACKGROUND", (0, 1), (-1, 1), LIGHT_GRAY),
        ("BOX", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 6 * mm))

    # ── INFORMACIÓN DEL CLIENTE ──
    elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", styles["SectionH"]))
    nombre_cliente = (
        f"{huesped.usuario.nombre} {huesped.usuario.apellido}"
        if huesped and huesped.usuario else "No disponible"
    )
    documento = huesped.documento_id if huesped else "No disponible"
    tipo_doc = huesped.tipo_documento if huesped else "CC"
    email_cliente = (
        huesped.usuario.email if huesped and huesped.usuario else "No disponible"
    )
    cliente_data = [
        [Paragraph("Nombre", styles["CellLabel"]),
         Paragraph(nombre_cliente, styles["CellValue"]),
         Paragraph("Documento", styles["CellLabel"]),
         Paragraph(f"{tipo_doc} {documento}", styles["CellValue"])],
        [Paragraph("Email", styles["CellLabel"]),
         Paragraph(email_cliente, styles["CellValue"]), "", ""],
    ]
    t_cliente = Table(cliente_data, colWidths=[24 * mm, 73 * mm, 24 * mm, 55 * mm])
    t_cliente.setStyle(TableStyle([
        ("SPAN", (1, 1), (-1, 1)),
        ("BOX", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_cliente)
    elements.append(Spacer(1, 6 * mm))

    # ── DETALLE DE LA ESTANCIA ──
    elements.append(Paragraph("DETALLE DE LA ESTANCIA", styles["SectionH"]))
    estancia_data = [
        [Paragraph("Habitación", styles["CellLabel"]),
         Paragraph(f"N° {habitacion.numero} — {habitacion.tipo.value}", styles["CellValue"]),
         Paragraph("Noches", styles["CellLabel"]),
         Paragraph(str(reserva.noches), styles["CellValue"])],
        [Paragraph("Entrada", styles["CellLabel"]),
         Paragraph(reserva.fecha_entrada.strftime("%Y-%m-%d"), styles["CellValue"]),
         Paragraph("Salida", styles["CellLabel"]),
         Paragraph(reserva.fecha_salida.strftime("%Y-%m-%d"), styles["CellValue"])],
    ]
    t_estancia = Table(estancia_data, colWidths=[24 * mm, 73 * mm, 24 * mm, 55 * mm])
    t_estancia.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_estancia)
    elements.append(Spacer(1, 8 * mm))

    # ── RESUMEN DE CARGOS ──
    elements.append(Paragraph("RESUMEN DE CARGOS", styles["SectionH"]))

    servicios = (
        db.session.execute(select(ServicioAdicional).filter_by(id_reserva=reserva.id))
        .scalars().all()
    )

    resumen_data = [
        [Paragraph("CONCEPTO", styles["CellLabel"]),
         Paragraph("DETALLE", styles["CellLabel"]),
         Paragraph("VALOR", styles["CellLabel"])],
        [Paragraph("Hospedaje (Subtotal)", styles["CellValue"]),
         Paragraph(f"{reserva.noches} noches x ${float(habitacion.precio_noche):,.2f}", styles["CellValue"]),
         Paragraph(f"${float(reserva.subtotal):,.2f}", styles["CellValue"])],
        [Paragraph("IVA 19%", styles["CellValue"]),
         Paragraph("Impuesto sobre alojamiento", styles["CellValue"]),
         Paragraph(f"${float(reserva.impuestos):,.2f}", styles["CellValue"])],
    ]

    if servicios:
        resumen_data.append([
            Paragraph("SERVICIOS ADICIONALES", styles["CellLabel"]), "", ""
        ])
        for s in servicios:
            resumen_data.append([
                Paragraph(f"  {s.tipo.value}", styles["CellValue"]),
                Paragraph(s.descripcion or "", styles["CellValue"]),
                Paragraph(f"${float(s.costo):,.2f}", styles["CellValue"]),
            ])

    total_general = (
        float(reserva.subtotal) + float(reserva.impuestos)
        + float(factura.servicios_adicionales_total)
    )
    resumen_data.append(["", "", ""])
    resumen_data.append([
        Paragraph("TOTAL A PAGAR", ParagraphStyle("TotalLabel",
            fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor(GOLD))),
        "",
        Paragraph(f"${total_general:,.2f}", ParagraphStyle("TotalVal",
            fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor(GOLD))),
    ])

    t_resumen = Table(resumen_data, colWidths=[55 * mm, 78 * mm, 43 * mm])
    t_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK)),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(LIGHT)),
        ("BOX", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LIGHT_GRAY),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_resumen)
    elements.append(Spacer(1, 10 * mm))

    # ── ESTADO DE PAGO ──
    elements.append(Paragraph("ESTADO DE PAGO", styles["SectionH"]))
    estado_texto = f"PENDIENTE DE PAGO — Total adeudado: ${total_general:,.2f}"
    if factura.estado.value == "Pagada":
        estado_texto = f"PAGADA — Total cancelado: ${total_general:,.2f}"
    elif factura.estado.value == "Emitida":
        estado_texto = f"EMITIDA — Pendiente de pago: ${total_general:,.2f}"
    elif factura.estado.value == "Anulada":
        estado_texto = "ANULADA"
    elements.append(Paragraph(estado_texto, styles["Normal"]))
    elements.append(Spacer(1, 6 * mm))

    # ── Línea separadora ──
    line_data2 = [[""]]
    t_line2 = Table(line_data2, colWidths=[174 * mm])
    t_line2.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_line2)

    # ── PIE DE PÁGINA ──
    elements.append(Paragraph(
        "HotelBook Pro — Av. Principal 123, Pereira, Risaralda, Colombia<br/>"
        "NIT: 123.456.789-0 — Tel: (606) 123 4567 — Email: hotelbook@example.com",
        styles["FooterText"],
    ))
    elements.append(Paragraph(
        "Gracias por su preferencia. Esta factura es un documento oficial de HotelBook Pro.",
        styles["FooterText"],
    ))

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
