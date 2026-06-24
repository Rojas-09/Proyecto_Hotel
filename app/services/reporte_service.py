"""
Reporte Service - Lógica de negocio para reportes (RF-08)
Genera reportes de ocupación, ingresos y estadísticas en formato xlsx y pdf.
"""

import os
from datetime import date, datetime
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from sqlalchemy import func, select
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app import db
from app.models.habitacion import Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.pago import EstadoPago, Pago
from app.models.reserva import EstadoReserva, Reserva


def _crear_directorio_reportes() -> str:
    """Crea y retorna la ruta del directorio de reportes."""
    directorio = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "static",
        "reportes",
    )
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    return directorio


def _parse_fecha(fecha_str: str) -> date:
    """Convierte string YYYY-MM-DD a objeto date."""
    return datetime.strptime(fecha_str, "%Y-%m-%d").date()


def _fecha_str(fecha: date) -> str:
    """Convierte date a string YYYY-MM-DD."""
    return fecha.strftime("%Y-%m-%d")


def _formatear_numero(valor) -> float:
    """Convierte Decimal o número a float."""
    if isinstance(valor, Decimal):
        return float(valor)
    return float(valor)


# ---------------------------------------------------------------------------
# Helpers de generación de archivos
# ---------------------------------------------------------------------------

def _generar_xlsx(datos: list, nombre_archivo: str, encabezados: list) -> str:
    """
    Genera un archivo xlsx con datos y encabezados dados.
    Retorna la ruta del archivo creado.
    """
    directorio = _crear_directorio_reportes()
    ruta = os.path.join(directorio, nombre_archivo)

    wb = Workbook()
    ws = wb.active
    ws.title = nombre_archivo.replace(".xlsx", "")[:31]

    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for col_idx, encabezado in enumerate(encabezados, 1):
        cell = ws.cell(row=1, column=col_idx, value=encabezado)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = border

    cell_align = Alignment(horizontal="left", vertical="center")
    for row_idx, fila in enumerate(datos, 2):
        for col_idx, valor in enumerate(fila, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=valor)
            cell.alignment = cell_align
            cell.border = border

    for col_idx in range(1, len(encabezados) + 1):
        max_length = max(
            len(str(ws.cell(row=r, column=col_idx).value or ""))
            for r in range(1, len(datos) + 2)
        )
        ws.column_dimensions[get_column_letter(col_idx)].width = min(
            max_length + 3, 40
        )

    wb.save(ruta)
    return ruta


def _generar_pdf(datos: list, nombre_archivo: str, titulo: str) -> str:
    """
    Genera un archivo pdf con una tabla de datos.
    Retorna la ruta del archivo creado.
    """
    directorio = _crear_directorio_reportes()
    ruta = os.path.join(directorio, nombre_archivo)

    doc = SimpleDocTemplate(
        ruta,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
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

    elements = []
    elements.append(Paragraph(titulo, styles["TitleCenter"]))
    elements.append(Spacer(1, 4 * mm))

    if not datos:
        elements.append(Paragraph("No hay datos disponibles para este reporte.", styles["Normal"]))
    else:
        encabezados = datos[0]
        filas = datos[1:]

        table_data = [encabezados] + filas
        col_count = len(encabezados)
        col_width = (210 * mm - 30 * mm) / col_count

        tabla = Table(table_data, colWidths=[col_width] * col_count)
        tabla.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(tabla)

    doc.build(elements)
    return ruta


# ---------------------------------------------------------------------------
# Reporte de Ocupación
# ---------------------------------------------------------------------------

def generar_ocupacion(
    fecha_inicio: str, fecha_fin: str, formato: str = "xlsx",
    creado_por: int = None
) -> dict:
    """
    Genera reporte de ocupación de habitaciones.
    Incluye: habitaciones ocupadas vs disponibles,
    porcentaje de ocupación por tipo, días promedio de estancia.
    """
    inicio = _parse_fecha(fecha_inicio)
    fin = _parse_fecha(fecha_fin)

    if inicio > fin:
        raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin.")

    reservas_periodo = db.session.execute(
        select(Reserva).filter(
            Reserva.fecha_entrada >= inicio,
            Reserva.fecha_entrada <= fin,
            Reserva.estado.in_([EstadoReserva.ocupada, EstadoReserva.completada]),
        )
    ).scalars().all()

    total_habitaciones = db.session.execute(
        select(func.count()).select_from(Habitacion).filter_by(activo=True)
    ).scalar()
    total_reservas = len(reservas_periodo)

    reservas_por_tipo = {}
    for tipo in TipoHabitacion:
        reservas_tipo = [r for r in reservas_periodo if r.habitacion.tipo == tipo]
        total_tipo = db.session.execute(
            select(func.count()).select_from(Habitacion)
            .filter_by(tipo=tipo, activo=True)
        ).scalar()
        ocupacion_tipo = (len(reservas_tipo) / total_tipo * 100) if total_tipo > 0 else 0
        reservas_por_tipo[tipo.value] = {
            "reservas": len(reservas_tipo),
            "habitaciones_total": total_tipo,
            "porcentaje_ocupacion": round(ocupacion_tipo, 2),
        }

    dias_totales = sum(r.noches for r in reservas_periodo)
    dias_promedio = round(dias_totales / total_reservas, 2) if total_reservas > 0 else 0

    ocupacion_general = (
        round(total_reservas / total_habitaciones * 100, 2)
        if total_habitaciones > 0 else 0
    )

    datos_xlsx = [
        ["Tipo de Habitación", "Habitaciones", "Reservas",
         "Ocupación (%)"],
    ]
    for tipo, info in reservas_por_tipo.items():
        datos_xlsx.append([
            tipo,
            info["habitaciones_total"],
            info["reservas"],
            info["porcentaje_ocupacion"],
        ])
    datos_xlsx.append(["", "", "", ""])
    datos_xlsx.append(["RESUMEN", "", "", ""])
    datos_xlsx.append(["Total habitaciones activas", total_habitaciones, "", ""])
    datos_xlsx.append(["Total reservas en período", total_reservas, "", ""])
    datos_xlsx.append(["Ocupación general (%)", ocupacion_general, "", ""])
    datos_xlsx.append(["Días promedio de estancia", dias_promedio, "", ""])

    nombre_archivo = f"ocupacion_{fecha_inicio}_{fecha_fin}.{formato}"
    if formato == "pdf":
        datos_pdf = [
            ["Tipo", "Habitaciones", "Reservas", "Ocupación (%)"],
        ]
        for tipo, info in reservas_por_tipo.items():
            datos_pdf.append([
                tipo, info["habitaciones_total"],
                info["reservas"], info["porcentaje_ocupacion"],
            ])
        ruta = _generar_pdf(datos_pdf, nombre_archivo, "Reporte de Ocupación")
    else:
        ruta = _generar_xlsx(
            datos_xlsx,
            nombre_archivo,
            ["Tipo de Habitación", "Habitaciones", "Reservas", "Ocupación (%)"],
        )

    reporte_registrado = None
    if creado_por:
        reporte_registrado = registrar_generado(
            tipo="ocupacion",
            formato=formato,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            archivo_path=ruta,
            archivo_nombre=nombre_archivo,
            creado_por=creado_por,
            resumen={
                "total_habitaciones": total_habitaciones,
                "total_reservas": total_reservas,
                "ocupacion_general": ocupacion_general,
                "dias_promedio": dias_promedio,
            },
        )

    return {
        "tipo": "ocupacion",
        "archivo": ruta,
        "formato": formato,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "resumen": {
            "total_habitaciones": total_habitaciones,
            "total_reservas": total_reservas,
            "ocupacion_general": ocupacion_general,
            "dias_promedio": dias_promedio,
        },
        "historial": reporte_registrado,
    }


# ---------------------------------------------------------------------------
# Reporte de Ingresos
# ---------------------------------------------------------------------------

def generar_ingresos(
    fecha_inicio: str, fecha_fin: str, formato: str = "xlsx",
    creado_por: int = None
) -> dict:
    """
    Genera reporte de ingresos por período.
    Incluye: total ingresos, desglose subtotal/IVA/servicios,
    ingresos por tipo de habitación.
    """
    inicio = _parse_fecha(fecha_inicio)
    fin = _parse_fecha(fecha_fin)

    if inicio > fin:
        raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin.")

    pagos_aprobados = db.session.execute(
        select(Pago).filter(
            Pago.fecha >= datetime.combine(inicio, datetime.min.time()),
            Pago.fecha <= datetime.combine(fin, datetime.max.time()),
            Pago.estado == EstadoPago.aprobado,
        )
    ).scalars().all()

    total_ingresos = sum(_formatear_numero(p.monto) for p in pagos_aprobados)

    ingresos_por_tipo = {}
    subtotal_total = Decimal("0.00")
    iva_total = Decimal("0.00")
    for tipo in TipoHabitacion:
        reservas_tipo = db.session.execute(
            select(Reserva).filter(
                Reserva.fecha_entrada >= inicio,
                Reserva.fecha_entrada <= fin,
                Reserva.habitacion.has(tipo=tipo),
                Reserva.estado.in_([
                    EstadoReserva.ocupada,
                    EstadoReserva.completada,
                    EstadoReserva.confirmada,
                ]),
            )
        ).scalars().all()

        total_tipo = Decimal("0.00")
        servicios_tipo = Decimal("0.00")
        for r in reservas_tipo:
            pagos_reserva = [
                p for p in pagos_aprobados if p.id_reserva == r.id
            ]
            total_tipo += sum(Decimal(str(p.monto)) for p in pagos_reserva)
            servicios_tipo += sum(
                Decimal(str(s.costo)) for s in r.servicios_adicionales
            )
            # Sumar usando Decimal para evitar mezclar floats y Decimals
            subtotal_total += Decimal(str(r.subtotal))
            iva_total += Decimal(str(r.impuestos))

        ingresos_por_tipo[tipo.value] = {
            "ingresos": _formatear_numero(total_tipo),
            "servicios": _formatear_numero(servicios_tipo),
            "reservas": len(reservas_tipo),
        }

    datos_xlsx = [
        ["Tipo de Habitación", "Reservas", "Servicios Adicionales ($)",
         "Ingresos ($)"],
    ]
    for tipo, info in ingresos_por_tipo.items():
        datos_xlsx.append([
            tipo,
            info["reservas"],
            info["servicios"],
            info["ingresos"],
        ])
    datos_xlsx.append(["", "", "", ""])
    datos_xlsx.append(["RESUMEN", "", "", ""])
    datos_xlsx.append(["Total ingresos", "", "", round(total_ingresos, 2)])
    datos_xlsx.append(["Subtotal acumulado", "", "", round(subtotal_total, 2)])
    datos_xlsx.append(["IVA acumulado", "", "", round(iva_total, 2)])
    datos_xlsx.append(["Total transacciones", len(pagos_aprobados), "", ""])

    nombre_archivo = f"ingresos_{fecha_inicio}_{fecha_fin}.{formato}"
    if formato == "pdf":
        datos_pdf = [
            ["Tipo", "Reservas", "Servicios ($)", "Ingresos ($)"],
        ]
        for tipo, info in ingresos_por_tipo.items():
            datos_pdf.append([
                tipo, info["reservas"], info["servicios"], info["ingresos"],
            ])
        datos_pdf.append(["", "", "", ""])
        datos_pdf.append(["TOTAL", len(pagos_aprobados), "", round(total_ingresos, 2)])
        ruta = _generar_pdf(datos_pdf, nombre_archivo, "Reporte de Ingresos")
    else:
        ruta = _generar_xlsx(
            datos_xlsx,
            nombre_archivo,
            ["Tipo de Habitación", "Reservas", "Servicios Adicionales ($)", "Ingresos ($)"],
        )

    reporte_registrado = None
    if creado_por:
        reporte_registrado = registrar_generado(
            tipo="ingresos",
            formato=formato,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            archivo_path=ruta,
            archivo_nombre=nombre_archivo,
            creado_por=creado_por,
            resumen={
                "total_ingresos": round(total_ingresos, 2),
                "subtotal": float(round(subtotal_total, 2)),
                "iva": float(round(iva_total, 2)),
                "transacciones": len(pagos_aprobados),
            },
        )

    return {
        "tipo": "ingresos",
        "archivo": ruta,
        "formato": formato,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "resumen": {
            "total_ingresos": round(total_ingresos, 2),
            "subtotal": float(round(subtotal_total, 2)),
            "iva": float(round(iva_total, 2)),
            "transacciones": len(pagos_aprobados),
        },
        "historial": reporte_registrado,
    }


# ---------------------------------------------------------------------------
# Reporte de Estadísticas
# ---------------------------------------------------------------------------

def generar_estadisticas(
    fecha_inicio: str, fecha_fin: str, formato: str = "xlsx",
    creado_por: int = None
) -> dict:
    """
    Genera reporte de estadísticas generales.
    Incluye: reservas por estado, top 5 habitaciones más reservadas,
    huéspedes con más reservas.
    """
    inicio = _parse_fecha(fecha_inicio)
    fin = _parse_fecha(fecha_fin)

    if inicio > fin:
        raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin.")

    reservas_periodo = db.session.execute(
        select(Reserva).filter(
            Reserva.fecha_entrada >= inicio,
            Reserva.fecha_entrada <= fin,
        )
    ).scalars().all()

    reservas_por_estado = {}
    for estado in EstadoReserva:
        count = sum(1 for r in reservas_periodo if r.estado == estado)
        reservas_por_estado[estado.value] = count

    top_habitaciones = (
        db.session.query(
            Habitacion.numero,
            Habitacion.tipo,
            func.count(Reserva.id).label("total"),
        )
        .join(Reserva, Reserva.id_habitacion == Habitacion.id)
        .filter(
            Reserva.fecha_entrada >= inicio,
            Reserva.fecha_entrada <= fin,
        )
        .group_by(Habitacion.id, Habitacion.numero, Habitacion.tipo)
        .order_by(func.count(Reserva.id).desc())
        .limit(5)
        .all()
    )

    top_huespedes = (
        db.session.query(
            Huesped.documento_id,
            Huesped.tipo_documento,
            Huesped.id.label("huesped_id"),
            func.count(Reserva.id).label("total"),
        )
        .join(Reserva, Reserva.id_huesped == Huesped.id)
        .filter(
            Reserva.fecha_entrada >= inicio,
            Reserva.fecha_entrada <= fin,
        )
        .group_by(Huesped.id, Huesped.documento_id, Huesped.tipo_documento)
        .order_by(func.count(Reserva.id).desc())
        .limit(5)
        .all()
    )

    datos_xlsx = [
        ["RESERVAS POR ESTADO", "", "", ""],
        ["Estado", "Cantidad", "", ""],
    ]
    for estado, cantidad in reservas_por_estado.items():
        datos_xlsx.append([estado, cantidad, "", ""])
    datos_xlsx.append(["", "", "", ""])

    datos_xlsx.append(["TOP 5 HABITACIONES MÁS RESERVADAS", "", "", ""])
    datos_xlsx.append(["Habitación", "Tipo", "Reservas", ""])
    for h in top_habitaciones:
        datos_xlsx.append([h.numero, h.tipo.value, h.total, ""])
    datos_xlsx.append(["", "", "", ""])

    datos_xlsx.append(["TOP 5 HUÉSPEDES CON MÁS RESERVAS", "", "", ""])
    datos_xlsx.append(["Documento", "Tipo", "Nombre", "Reservas"])
    for h in top_huespedes:
        huesped_obj = db.session.get(Huesped, h.huesped_id)
        nombre = (
            f"{huesped_obj.usuario.nombre} {huesped_obj.usuario.apellido}"
            if huesped_obj and huesped_obj.usuario else "N/A"
        )
        datos_xlsx.append([h.documento_id, h.tipo_documento, nombre, h.total])

    nombre_archivo = f"estadisticas_{fecha_inicio}_{fecha_fin}.{formato}"
    if formato == "pdf":
        datos_pdf = [["Sección", "Detalle", "Valor", ""]]
        datos_pdf.append(["Total reservas", str(len(reservas_periodo)), "", ""])
        datos_pdf.append(["", "", "", ""])
        datos_pdf.append(["ESTADO", "CANTIDAD", "", ""])
        for estado, cantidad in reservas_por_estado.items():
            datos_pdf.append([estado, str(cantidad), "", ""])
        datos_pdf.append(["", "", "", ""])
        datos_pdf.append(["HABITACIÓN", "TIPO", "RESERVAS", ""])
        for h in top_habitaciones:
            datos_pdf.append([h.numero, h.tipo.value, str(h.total), ""])
        datos_pdf.append(["", "", "", ""])
        datos_pdf.append(["DOCUMENTO", "NOMBRE", "RESERVAS", ""])
        for h in top_huespedes:
            huesped_obj = db.session.get(Huesped, h.huesped_id)
            nombre = (
                f"{huesped_obj.usuario.nombre} {huesped_obj.usuario.apellido}"
                if huesped_obj and huesped_obj.usuario else "N/A"
            )
            datos_pdf.append([h.documento_id, nombre, str(h.total), ""])
        ruta = _generar_pdf(datos_pdf, nombre_archivo, "Reporte de Estadísticas")
    else:
        ruta = _generar_xlsx(
            datos_xlsx,
            nombre_archivo,
            ["Concepto", "Detalle 1", "Detalle 2", "Valor"],
        )

    reporte_registrado = None
    if creado_por:
        reporte_registrado = registrar_generado(
            tipo="estadisticas",
            formato=formato,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            archivo_path=ruta,
            archivo_nombre=nombre_archivo,
            creado_por=creado_por,
            resumen={
                "total_reservas": len(reservas_periodo),
                "reservas_por_estado": reservas_por_estado,
            },
        )

    return {
        "tipo": "estadisticas",
        "archivo": ruta,
        "formato": formato,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "resumen": {
            "total_reservas": len(reservas_periodo),
            "reservas_por_estado": reservas_por_estado,
        },
        "historial": reporte_registrado,
    }


def registrar_generado(tipo: str, formato: str, fecha_inicio: str, fecha_fin: str,
                       archivo_path: str, archivo_nombre: str, creado_por: int,
                       resumen: dict = None) -> dict:
    """Registra un reporte generado en el historial."""
    from app.models.reporte import ReporteGenerado
    from datetime import date

    reporte = ReporteGenerado(
        tipo=tipo,
        formato=formato,
        fecha_inicio=date.fromisoformat(fecha_inicio),
        fecha_fin=date.fromisoformat(fecha_fin),
        archivo_path=archivo_path,
        archivo_nombre=archivo_nombre,
        creado_por=creado_por,
        resumen=resumen,
    )
    db.session.add(reporte)
    db.session.flush()
    return reporte.to_dict()


def listar_historial(filtros=None):
    """Lista el historial de reportes generados con filtros opcionales."""
    from app.models.reporte import ReporteGenerado

    query = ReporteGenerado.query

    if filtros:
        if filtros.get("tipo"):
            query = query.filter_by(tipo=filtros["tipo"])

        if filtros.get("formato"):
            query = query.filter_by(formato=filtros["formato"])

        if filtros.get("creado_por"):
            query = query.filter_by(creado_por=int(filtros["creado_por"]))

        if filtros.get("fecha_desde"):
            from datetime import date
            fecha = date.fromisoformat(filtros["fecha_desde"])
            query = query.filter(ReporteGenerado.created_at >= fecha)

        if filtros.get("fecha_hasta"):
            from datetime import date
            fecha = date.fromisoformat(filtros["fecha_hasta"])
            query = query.filter(ReporteGenerado.created_at <= fecha)

    reportes = query.order_by(ReporteGenerado.created_at.desc()).all()
    return [r.to_dict() for r in reportes]
