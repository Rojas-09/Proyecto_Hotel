"""
Test de integración — Flujo completo HotelBook Pro.
Cubre: login → crear reserva → garantía → checkin → servicios →
liquidación → checkout → puntos → factura → descarga PDF.
"""
import pytest
from datetime import date, timedelta

from app import db
from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.huesped import Huesped
from app.models.usuario import RolEnum, Usuario
from app.models.puntos_fidelidad import PuntosFidelidad


@pytest.fixture
def seed(app):
    """Crea datos semilla para el flujo completo."""
    with app.app_context():
        admin = Usuario(nombre="Admin", apellido="Root",
                        email="admin@h.com", rol=RolEnum.admin)
        admin.password = "Admin123!"
        db.session.add(admin)
        cli = Usuario(nombre="Juan", apellido="Pérez",
                      email="juan@h.com", rol=RolEnum.cliente)
        cli.password = "Pass123!"
        db.session.add(cli)
        db.session.flush()
        huesped = Huesped(id_usuario=cli.id, documento_id="CC12345678")
        db.session.add(huesped)
        hab = Habitacion(numero="INT-1", tipo=TipoHabitacion.doble,
                         precio_noche=200000, capacidad=2, piso=1,
                         estado=EstadoHabitacion.disponible)
        db.session.add(hab)
        db.session.commit()
        return {"habitacion_id": hab.id, "huesped_id": huesped.id,
                "usuario_id": cli.id}


def _login(client, email, password):
    resp = client.post("/api/v1/auth/login", json={
        "email": email, "password": password})
    assert resp.status_code == 200
    token = resp.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


class TestFlujoCompleto:
    """Ejecuta la cadena completa de una reserva."""

    def test_flujo_integral(self, client, app, seed):
        with app.app_context():
            admin_h = _login(client, "admin@h.com", "Admin123!")
            cliente_h = _login(client, "juan@h.com", "Pass123!")

            fe = (date.today() + timedelta(days=1)).isoformat()
            fs = (date.today() + timedelta(days=3)).isoformat()

            # 1. Crear reserva
            r = client.post("/api/v1/reservas/", json={
                "id_habitacion": seed["habitacion_id"],
                "fecha_entrada": fe, "fecha_salida": fs,
            }, headers=cliente_h)
            assert r.status_code == 201, f"Crear reserva: {r.get_json()}"
            rid = r.get_json()["data"]["id"]

            # 2. Garantía
            r = client.post(f"/api/v1/pagos/garantia/{rid}",
                            json={"metodo": "Efectivo"}, headers=cliente_h)
            assert r.status_code == 201, f"Garantía: {r.get_json()}"

            # 3. Check-in
            r = client.put(f"/api/v1/reservas/{rid}/checkin",
                           headers=admin_h)
            assert r.status_code == 200, f"Check-in: {r.get_json()}"
            assert "Ocupada" in str(r.get_json()["data"]["estado"])

            # 4. Servicio comedor
            r = client.post(f"/api/v1/reservas/{rid}/servicios",
                            json={"tipo": "comedor",
                                  "descripcion": "Cena ejecutiva",
                                  "costo": 85000},
                            headers=admin_h)
            assert r.status_code == 201, f"Servicio comedor: {r.get_json()}"

            # 5. Servicio spa
            r = client.post(f"/api/v1/reservas/{rid}/servicios",
                            json={"tipo": "spa",
                                  "descripcion": "Masaje relajante",
                                  "costo": 120000},
                            headers=admin_h)
            assert r.status_code == 201, f"Servicio spa: {r.get_json()}"

            # 6. Liquidación
            r = client.post(f"/api/v1/pagos/liquidacion/{rid}",
                            json={"metodo": "Efectivo"}, headers=admin_h)
            assert r.status_code == 201, f"Liquidación: {r.get_json()}"

            # 7. Check-out
            r = client.put(f"/api/v1/reservas/{rid}/checkout",
                           headers=admin_h)
            assert r.status_code == 200, f"Check-out: {r.get_json()}"
            puntos = r.get_json()["data"]["puntos_ganados"]
            assert puntos > 0

            # 8. Verificar puntos en historial
            reg = db.session.execute(
                db.select(PuntosFidelidad).filter_by(id_reserva=rid)
            ).scalar_one_or_none()
            assert reg is not None, "No hay registro de puntos"
            assert reg.puntos == puntos

            # 9. Emitir factura
            r = client.post(f"/api/v1/facturas/reserva/{rid}/emitir",
                            headers=admin_h)
            assert r.status_code == 201, f"Emitir factura: {r.get_json()}"
            assert r.get_json()["data"]["estado"] == "Emitida"

            # 10. Descargar PDF
            r = client.get(f"/api/v1/facturas/reserva/{rid}/descargar",
                           headers=admin_h)
            assert r.status_code == 200, f"Descargar PDF: {r.status_code}"
            assert r.content_type == "application/pdf"
            assert r.data[:4] == b"%PDF"