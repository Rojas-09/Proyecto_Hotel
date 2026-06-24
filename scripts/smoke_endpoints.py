"""
Smoke test de endpoints mínimos para presentación.
Ejecutar: `source venv/bin/activate && python scripts/smoke_endpoints.py`
"""

from datetime import date, timedelta
from decimal import Decimal
from pprint import pprint

from app import create_app, db

app = create_app("testing")

with app.app_context():
    client = app.test_client()

    def post(url, json=None, token=None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return client.post(url, json=json, headers=headers)

    def get(url, token=None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return client.get(url, headers=headers)

    def put(url, json=None, token=None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return client.put(url, json=json, headers=headers)

    def delete(url, token=None):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return client.delete(url, headers=headers)

    print("--- Register admin ---")
    r = post(
        "/api/v1/auth/register-admin",
        json={
            "nombre": "SmokeAdmin",
            "apellido": "X",
            "email": "smoke_admin@example.com",
            "password": "Pass1234!",
        },
    )
    print("status", r.status_code)
    data = r.get_json()
    pprint(data)
    token = None
    if r.status_code in (200, 201):
        token = data.get("data", {}).get("token")

    # Create room
    print("\n--- Create habitacion ---")
    # Include trailing slash to match blueprint route definitions
    rh = post(
        "/api/v1/habitaciones/",
        json={
            "numero": "9101",
            "tipo": "doble",
            "precio_noche": 100000,
            "capacidad": 2,
        },
        token=token,
    )
    print("status", rh.status_code, rh.get_json())

    # Register cliente
    print("\n--- Register cliente ---")
    rc = post(
        "/api/v1/auth/register",
        json={
            "nombre": "Smoke",
            "apellido": "Cli",
            "email": "smoke_cli@example.com",
            "password": "Pass1234!",
            "documento_id": "CC99999",
        },
    )
    print("status", rc.status_code, rc.get_json())

    # Login cliente
    print("\n--- Login cliente ---")
    rl = post(
        "/api/v1/auth/login",
        json={"email": "smoke_cli@example.com", "password": "Pass1234!"},
    )
    print("status", rl.status_code, rl.get_json())
    token_cli = rl.get_json().get("data", {}).get("token")

    # Create reserva by cliente
    print("\n--- Crear reserva (cliente) ---")
    hoy = date.today()
    # Include trailing slash for reservas create route
    rres = post(
        "/api/v1/reservas/",
        json={
            "id_habitacion": 1,
            "fecha_entrada": hoy.isoformat(),
            "fecha_salida": (hoy + timedelta(days=2)).isoformat(),
            "id_huesped": 1,
        },
        token=token_cli,
    )
    print("status", rres.status_code, rres.get_json())
    reserva_id = rres.get_json().get("data", {}).get("id")

    # Procesar garantía (cliente) - debe hacerse mientras la reserva está Pendiente
    print("\n--- Procesar garantía (cliente) ---")
    rgar = post(
        f"/api/v1/pagos/garantia/{reserva_id}",
        json={"metodo": "Efectivo"},
        token=token_cli,
    )
    print("status", rgar.status_code, rgar.get_json())

    # Confirm reserva (admin) - (procesar_garantia normalmente setea a Confirmada)
    print("\n--- Confirmar reserva (admin) ---")
    rconf = put(f"/api/v1/reservas/{reserva_id}/confirmar", token=token)
    print("status", rconf.status_code, rconf.get_json())

    # Checkin (recepcionista role required normally) - use admin to act (PUT)
    print("\n--- Checkin (admin) ---")
    rcheck = put(f"/api/v1/reservas/{reserva_id}/checkin", token=token)
    print("status", rcheck.status_code, rcheck.get_json())

    # Agregar servicio (recepcionista/admin)
    print("\n--- Agregar servicio ---")
    ras = post(
        f"/api/v1/reservas/{reserva_id}/servicios",
        json={"tipo": "Comedor", "descripcion": "Desayuno smoke", "costo": 15000},
        token=token,
    )
    print("status", ras.status_code, ras.get_json())
    servicio_id = ras.get_json().get("data", {}).get("id")

    # Listar servicios
    print("\n--- Listar servicios ---")
    rlist = get(f"/api/v1/reservas/{reserva_id}/servicios", token=token)
    print("status", rlist.status_code, rlist.get_json())

    # Actualizar servicio
    print("\n--- Actualizar servicio ---")
    rput = put(f"/api/v1/servicios/{servicio_id}", json={"costo": 18000}, token=token)
    print("status", rput.status_code, rput.get_json())

    # Crear pago liquidacion (admin) - correct route is /api/v1/pagos/liquidacion/<reserva_id>
    print("\n--- Crear pago liquidacion (admin) ---")
    # First, process garantía (cliente pays 50%)
    print("\n--- Procesar garantía (cliente) ---")
    rgar = post(
        f"/api/v1/pagos/garantia/{reserva_id}",
        json={"metodo": "Efectivo"},
        token=token_cli,
    )
    print("status", rgar.status_code, rgar.get_json())

    rpago = post(
        f"/api/v1/pagos/liquidacion/{reserva_id}",
        json={"metodo": "Efectivo"},
        token=token,
    )
    print("status", rpago.status_code, rpago.get_json())

    # Hacer checkout (PUT)
    print("\n--- Checkout ---")
    rco = put(f"/api/v1/reservas/{reserva_id}/checkout", token=token)
    print("status", rco.status_code, rco.get_json())

    # Obtener factura
    print("\n--- Obtener factura ---")
    rf = get(f"/api/v1/facturas/reserva/{reserva_id}", token=token)
    print("status", rf.status_code, rf.get_json())

    # Generar reporte ingresos
    print("\n--- Generar reporte ingresos ---")
    rr = get(
        "/api/v1/reportes/ingresos?fecha_inicio=2020-01-01&fecha_fin=2030-01-01&formato=xlsx",
        token=token,
    )
    print("status", rr.status_code)
    if rr.status_code == 200:
        with open("/tmp/smoke_reporte_ingresos.xlsx", "wb") as f:
            f.write(rr.data)
        print("Reporte guardado en /tmp/smoke_reporte_ingresos.xlsx")

    print("\n--- Smoke tests finished ---")
