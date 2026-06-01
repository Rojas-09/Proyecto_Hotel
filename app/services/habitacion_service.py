from datetime import date, datetime

from sqlalchemy import func, select

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.utils.fecha_helper import ahora_colombia


def obtener_todas(filtros=None):
    habitaciones = db.session.execute(
        select(Habitacion).filter_by(activo=True)
    ).scalars().all()

    if filtros:
        if filtros.get("tipo"):
            try:
                tipo = TipoHabitacion(filtros["tipo"])
                habitaciones = [
                    h for h in habitaciones if h.tipo == tipo
                ]
            except ValueError:
                raise ValueError(
                    f"Tipo de habitacion invalido. "
                    f"Valores permitidos: {[t.value for t in TipoHabitacion]}"
                )
        if filtros.get("estado"):
            try:
                estado = EstadoHabitacion(filtros["estado"])
                habitaciones = [
                    h for h in habitaciones if h.estado == estado
                ]
            except ValueError:
                raise ValueError(
                    f"Estado invalido. "
                    f"Valores permitidos: {[e.value for e in EstadoHabitacion]}"
                )
        if filtros.get("piso"):
            habitaciones = [
                h for h in habitaciones if h.piso == int(filtros["piso"])
            ]

    return [h.to_dict() for h in habitaciones]


def obtener_por_id(habitacion_id):
    habitacion = db.session.execute(
        select(Habitacion).filter_by(id=habitacion_id, activo=True)
    ).scalar_one_or_none()
    if not habitacion:
        raise LookupError(f"Habitacion con id {habitacion_id} no encontrada.")
    return habitacion.to_dict()


def crear(datos):
    _validar_datos_obligatorios(datos)

    numero_normalizado = str(datos["numero"]).strip()

    existing = db.session.execute(
        select(Habitacion).filter(
            func.lower(func.trim(Habitacion.numero))
            == numero_normalizado.lower()
        )
    ).scalar_one_or_none()
    if existing:
        raise ValueError(
            f"Ya existe una habitacion con el numero '{numero_normalizado}'."
        )

    try:
        tipo = TipoHabitacion(datos["tipo"].lower())
    except ValueError:
        raise ValueError(
            f"Tipo invalido. Valores permitidos: "
            f"{[t.value for t in TipoHabitacion]}"
        )

    habitacion = Habitacion(
        numero=numero_normalizado,
        tipo=tipo,
        descripcion=datos.get("descripcion"),
        precio_noche=datos["precio_noche"],
        capacidad=int(datos["capacidad"]),
        piso=int(datos.get("piso", 1)),
        estado=EstadoHabitacion.disponible,
    )

    db.session.add(habitacion)
    db.session.commit()
    return habitacion.to_dict()


def actualizar(habitacion_id, datos):
    habitacion = db.session.execute(
        select(Habitacion).filter_by(id=habitacion_id, activo=True)
    ).scalar_one_or_none()
    if not habitacion:
        raise LookupError(f"Habitacion con id {habitacion_id} no encontrada.")

    if "numero" in datos and str(datos["numero"]).strip() != habitacion.numero:
        numero_normalizado = str(datos["numero"]).strip()
        existing = db.session.execute(
            select(Habitacion).filter(
                func.lower(func.trim(Habitacion.numero))
                == numero_normalizado.lower()
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError(
                f"Ya existe una habitacion con el numero '{numero_normalizado}'."
            )
        habitacion.numero = numero_normalizado

    if "tipo" in datos:
        try:
            habitacion.tipo = TipoHabitacion(datos["tipo"].lower())
        except ValueError:
            raise ValueError(
                f"Tipo invalido. Valores permitidos: "
                f"{[t.value for t in TipoHabitacion]}"
            )

    if "estado" in datos:
        try:
            habitacion.estado = EstadoHabitacion(datos["estado"].lower())
        except ValueError:
            raise ValueError(
                f"Estado invalido. Valores permitidos: "
                f"{[e.value for e in EstadoHabitacion]}"
            )

    if "descripcion" in datos:
        habitacion.descripcion = datos["descripcion"]

    if "precio_noche" in datos:
        if float(datos["precio_noche"]) <= 0:
            raise ValueError("El precio por noche debe ser mayor a 0.")
        habitacion.precio_noche = datos["precio_noche"]

    if "capacidad" in datos:
        if int(datos["capacidad"]) <= 0:
            raise ValueError("La capacidad debe ser mayor a 0.")
        habitacion.capacidad = int(datos["capacidad"])

    if "piso" in datos:
        habitacion.piso = int(datos["piso"])

    habitacion.updated_at = ahora_colombia()
    db.session.commit()
    return habitacion.to_dict()


def eliminar(habitacion_id):
    habitacion = db.session.execute(
        select(Habitacion).filter_by(id=habitacion_id, activo=True)
    ).scalar_one_or_none()
    if not habitacion:
        raise LookupError(f"Habitacion con id {habitacion_id} no encontrada.")

    habitacion.activo = False
    habitacion.updated_at = ahora_colombia()
    db.session.commit()
    return {"mensaje": f"Habitacion {habitacion.numero} eliminada correctamente."}


def buscar_disponibles(fecha_entrada_str, fecha_salida_str, tipo=None):
    try:
        fecha_entrada = datetime.strptime(fecha_entrada_str, "%Y-%m-%d").date()
        fecha_salida = datetime.strptime(fecha_salida_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(
            "Formato de fecha invalido. Use YYYY-MM-DD."
        )

    if fecha_entrada < date.today():
        raise ValueError("La fecha de entrada no puede ser en el pasado.")

    if fecha_entrada >= fecha_salida:
        raise ValueError(
            "La fecha de entrada debe ser anterior a la fecha de salida."
        )

    habitaciones = db.session.execute(
        select(Habitacion).filter_by(
            activo=True,
            estado=EstadoHabitacion.disponible
        )
    ).scalars().all()

    if tipo:
        try:
            tipo_enum = TipoHabitacion(tipo)
            habitaciones = [
                h for h in habitaciones if h.tipo == tipo_enum
            ]
        except ValueError:
            raise ValueError(
                f"Tipo invalido. Valores permitidos: "
                f"{[t.value for t in TipoHabitacion]}"
            )

    habitaciones = sorted(habitaciones, key=lambda h: h.precio_noche)

    resultado = []
    for h in habitaciones:
        data = h.to_dict()
        noches = (fecha_salida - fecha_entrada).days
        data["noches"] = noches
        data["total_estimado"] = round(float(h.precio_noche) * noches, 2)
        resultado.append(data)

    return resultado


def _validar_datos_obligatorios(datos):
    requeridos = ["numero", "tipo", "precio_noche", "capacidad"]
    faltantes = [c for c in requeridos if c not in datos or datos[c] == ""]
    if faltantes:
        raise ValueError(
            f"Campos obligatorios faltantes: {', '.join(faltantes)}"
        )

    if float(datos["precio_noche"]) <= 0:
        raise ValueError("El precio por noche debe ser mayor a 0.")

    if int(datos["capacidad"]) <= 0:
        raise ValueError("La capacidad debe ser mayor a 0.")
