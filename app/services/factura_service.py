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
    """Genera el PDF de la factura con un diseño más claro e itemizado."""
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

    # Tokens visuales del documento
    GOLD = colors.HexColor("#C8A45C")
    NAVY = colors.HexColor("#1E2A3A")
    SLATE = colors.HexColor("#2F3F52")
    INK = colors.HexColor("#2D3138")
    MUTED = colors.HexColor("#6B7280")
    BORDER = colors.HexColor("#E2E6EA")
    SOFT_BG = colors.HexColor("#F8FAFC")
    WHITE = colors.white

    def _money(value) -> str:
        return f"${float(value):,.2f}"

    def _date_or_dash(value, with_time=False) -> str:
        if not value:
            return "-"
        return value.strftime("%Y-%m-%d %H:%M") if with_time else value.strftime("%Y-%m-%d")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="HBPBrand",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=NAVY,
            leading=22,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HBPMuted",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leading=11,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HBPTitle",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=WHITE,
            alignment=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HBPSection",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=SLATE,
            spaceBefore=8,
            spaceAfter=3,
            leading=11,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HBPLabel",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=SLATE,
            leading=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HBPValue",
            fontName="Helvetica",
            fontSize=8,
            textColor=INK,
            leading=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HBPFooter",
            fontName="Helvetica",
            fontSize=7.5,
            textColor=MUTED,
            alignment=1,
            leading=10,
        )
    )

    elements = []

    # Encabezado principal
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "static",
        "logo.png",
    )
    logo_cell = Spacer(1, 0.1 * mm)
    if os.path.exists(logo_path):
        from reportlab.platypus import Image

        logo_cell = Image(logo_path, width=38 * mm, height=13 * mm)

    header_left = [
        logo_cell,
        Paragraph("HOTELBOOK PRO", styles["HBPBrand"]),
        Paragraph(
            "NIT: 123.456.789-0<br/>"
            "Av. Principal 123, Pereira<br/>"
            "Tel: (606) 123 4567 · hotelbook@example.com",
            styles["HBPMuted"],
        ),
    ]
    header_right = [
        Paragraph("FACTURA", styles["HBPBrand"]),
        Paragraph(f"No. {str(factura.id).zfill(8)}", styles["HBPValue"]),
        Paragraph(f"Reserva: {str(factura.id_reserva).zfill(6)}", styles["HBPValue"]),
        Paragraph(
            f"Emitida: {_date_or_dash(factura.fecha_emision, with_time=True)}",
            styles["HBPMuted"],
        ),
    ]

    header_data = [
        [header_left, header_right],
    ]
    t_header = Table(header_data, colWidths=[110 * mm, 66 * mm])
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 3 * mm))

    title_bar = Table([[Paragraph("FACTURA DE ALOJAMIENTO", styles["HBPTitle"]) ]], colWidths=[176 * mm])
    title_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(title_bar)
    elements.append(Spacer(1, 4 * mm))

    # Estado destacado
    estado_color = SLATE
    if factura.estado == EstadoFactura.pagada:
        estado_color = colors.HexColor("#0F766E")
    elif factura.estado == EstadoFactura.emitida:
        estado_color = colors.HexColor("#1D4ED8")
    elif factura.estado == EstadoFactura.pendiente:
        estado_color = colors.HexColor("#B45309")
    elif factura.estado == EstadoFactura.anulada:
        estado_color = colors.HexColor("#B91C1C")

    estado_box = Table(
        [[Paragraph(f"Estado de la factura: {factura.estado.value.upper()}", styles["HBPValue"]) ]],
        colWidths=[176 * mm],
    )
    estado_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 3, estado_color),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(estado_box)
    elements.append(Spacer(1, 5 * mm))

    # Datos de factura y cliente
    info_data = [
        [
            Paragraph("Comprobante", styles["HBPLabel"]),
            Paragraph(f"FACT-{str(factura.id).zfill(8)}", styles["HBPValue"]),
            Paragraph("Reserva", styles["HBPLabel"]),
            Paragraph(str(factura.id_reserva).zfill(6), styles["HBPValue"]),
        ],
        [
            Paragraph("Fecha de emisión", styles["HBPLabel"]),
            Paragraph(_date_or_dash(factura.fecha_emision, with_time=True), styles["HBPValue"]),
            Paragraph("Tipo", styles["HBPLabel"]),
            Paragraph("Factura electrónica interna", styles["HBPValue"]),
        ],
    ]
    t_info = Table(info_data, colWidths=[28 * mm, 45 * mm, 28 * mm, 45 * mm])
    t_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT_BG),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 5 * mm))

    elements.append(Paragraph("DATOS DEL HUÉSPED", styles["HBPSection"]))
    nombre_cliente = (
        f"{huesped.usuario.nombre} {huesped.usuario.apellido}"
        if huesped and huesped.usuario else "No disponible"
    )
    documento = huesped.documento_id if huesped else "No disponible"
    tipo_doc = huesped.tipo_documento if huesped else "CC"
    email_cliente = (
        huesped.usuario.email if huesped and huesped.usuario else "No disponible"
    )
    telefono_cliente = (
        huesped.usuario.telefono if huesped and huesped.usuario and huesped.usuario.telefono
        else "No disponible"
    )
    cliente_data = [
        [
            Paragraph("Nombre", styles["HBPLabel"]),
            Paragraph(nombre_cliente, styles["HBPValue"]),
            Paragraph("Documento", styles["HBPLabel"]),
            Paragraph(f"{tipo_doc} {documento}", styles["HBPValue"]),
        ],
        [
            Paragraph("Email", styles["HBPLabel"]),
            Paragraph(email_cliente, styles["HBPValue"]),
            Paragraph("Teléfono", styles["HBPLabel"]),
            Paragraph(telefono_cliente, styles["HBPValue"]),
        ],
    ]
    t_cliente = Table(cliente_data, colWidths=[24 * mm, 70 * mm, 24 * mm, 58 * mm])
    t_cliente.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_cliente)
    elements.append(Spacer(1, 5 * mm))

    elements.append(Paragraph("DETALLE DE ESTANCIA", styles["HBPSection"]))
    estancia_data = [
        [
            Paragraph("Habitación", styles["HBPLabel"]),
            Paragraph(
                (
                    f"N° {habitacion.numero} · {habitacion.tipo.value}"
                    if habitacion else "No disponible"
                ),
                styles["HBPValue"],
            ),
            Paragraph("Noches", styles["HBPLabel"]),
            Paragraph(str(reserva.noches or 0), styles["HBPValue"]),
        ],
        [
            Paragraph("Entrada", styles["HBPLabel"]),
            Paragraph(_date_or_dash(reserva.fecha_entrada), styles["HBPValue"]),
            Paragraph("Salida", styles["HBPLabel"]),
            Paragraph(_date_or_dash(reserva.fecha_salida), styles["HBPValue"]),
        ],
    ]
    t_estancia = Table(estancia_data, colWidths=[24 * mm, 73 * mm, 24 * mm, 55 * mm])
    t_estancia.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_estancia)
    elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph("DETALLE DE CARGOS", styles["HBPSection"]))

    servicios = (
        db.session.execute(select(ServicioAdicional).filter_by(id_reserva=reserva.id))
        .scalars().all()
    )
    subtotal = Decimal(str(factura.subtotal))
    impuestos = Decimal(str(factura.impuestos))
    servicios_total = Decimal(str(factura.servicios_adicionales_total))
    total_general = Decimal(str(factura.total))

    precio_noche = Decimal(str(habitacion.precio_noche)) if habitacion else Decimal("0")

    detalle_rows = [
        [
            Paragraph("ITEM", styles["HBPLabel"]),
            Paragraph("DESCRIPCIÓN", styles["HBPLabel"]),
            Paragraph("CANT.", styles["HBPLabel"]),
            Paragraph("V. UNITARIO", styles["HBPLabel"]),
            Paragraph("TOTAL", styles["HBPLabel"]),
        ],
        [
            Paragraph("Hospedaje", styles["HBPValue"]),
            Paragraph(
                f"{reserva.noches} noche(s) · Habitación {habitacion.numero if habitacion else '-'}",
                styles["HBPValue"],
            ),
            Paragraph(str(reserva.noches or 0), styles["HBPValue"]),
            Paragraph(_money(precio_noche), styles["HBPValue"]),
            Paragraph(_money(subtotal), styles["HBPValue"]),
        ],
    ]

    for servicio in servicios:
        detalle_rows.append(
            [
                Paragraph(f"Servicio · {servicio.tipo.value}", styles["HBPValue"]),
                Paragraph(servicio.descripcion or "Servicio adicional", styles["HBPValue"]),
                Paragraph("1", styles["HBPValue"]),
                Paragraph(_money(servicio.costo), styles["HBPValue"]),
                Paragraph(_money(servicio.costo), styles["HBPValue"]),
            ]
        )

    detalle_table = Table(
        detalle_rows,
        colWidths=[30 * mm, 72 * mm, 16 * mm, 26 * mm, 32 * mm],
        repeatRows=1,
    )
    detalle_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("ALIGN", (2, 1), (4, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SOFT_BG]),
    ]))
    elements.append(detalle_table)
    elements.append(Spacer(1, 5 * mm))

    saldo = Decimal("0.00") if factura.estado == EstadoFactura.pagada else total_general
    resumen_financiero = [
        [Paragraph("Subtotal hospedaje", styles["HBPValue"]), Paragraph(_money(subtotal), styles["HBPValue"])],
        [Paragraph("IVA", styles["HBPValue"]), Paragraph(_money(impuestos), styles["HBPValue"])],
        [Paragraph("Servicios adicionales", styles["HBPValue"]), Paragraph(_money(servicios_total), styles["HBPValue"])],
        [Paragraph("TOTAL FACTURA", styles["HBPLabel"]), Paragraph(_money(total_general), styles["HBPLabel"])],
        [Paragraph("Saldo por pagar", styles["HBPLabel"]), Paragraph(_money(saldo), styles["HBPLabel"])],
    ]
    resumen_table = Table(resumen_financiero, colWidths=[104 * mm, 72 * mm])
    resumen_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#EFF6FF")),
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#FFFBEB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(resumen_table)
    elements.append(Spacer(1, 7 * mm))

    # Pie legal
    condiciones = Table(
        [[
            Paragraph(
                "Observaciones: Esta factura refleja los cargos de alojamiento y servicios "
                "registrados en la reserva. Para solicitudes de aclaración contacte al área "
                "de facturación del hotel.",
                styles["HBPMuted"],
            )
        ]],
        colWidths=[176 * mm],
    )
    condiciones.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT_BG),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(condiciones)
    elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph(
        "HotelBook Pro — Av. Principal 123, Pereira, Risaralda, Colombia<br/>"
        "NIT: 123.456.789-0 — Tel: (606) 123 4567 — Email: hotelbook@example.com",
        styles["HBPFooter"],
    ))
    elements.append(Paragraph(
        "Gracias por su preferencia. Esta factura es un documento oficial de HotelBook Pro.",
        styles["HBPFooter"],
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
