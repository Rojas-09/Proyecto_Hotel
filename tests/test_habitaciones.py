"""
Tests del Modulo Habitaciones - HotelBook Pro
Ejecutar: pytest tests/test_habitaciones.py -v
"""

import pytest

from app.models.habitacion import EstadoHabitacion, Habitacion, TipoHabitacion
from app.models.usuario import Usuario, RolEnum
from app import db


@pytest.fixture
def habitacion_data():
    return {
        "numero": "101",
        "tipo": "Simple",
        "descripcion": "Habitacion simple con vista al jardin",
        "precio_noche": 150000.00,
        "capacidad": 1,
        "piso": 1,
    }


@pytest.fixture
def habitacion_en_db(app, habitacion_data, request):
    """Crea una habitación con número único por test."""
    # Usar el test name como parte del numero para hacerlo único
    unique_numero = f"{habitacion_data['numero']}{request.node.name[-2:]}"
    with app.app_context():
        h = Habitacion(
            numero=unique_numero,
            tipo=TipoHabitacion.simple,
            descripcion=habitacion_data["descripcion"],
            precio_noche=habitacion_data["precio_noche"],
            capacidad=habitacion_data["capacidad"],
            piso=habitacion_data["piso"],
            estado=EstadoHabitacion.disponible,
        )
        db.session.add(h)
        db.session.commit()
        result = h.to_dict()
    yield result
    with app.app_context():
        db.session.query(Habitacion).filter_by(numero=unique_numero).delete()
        db.session.commit()


@pytest.fixture
def admin_headers(client, request, app):
    """Crea un admin usando register-admin (para el primer admin) o usuarios endpoint."""
    email = f"admin_hab_{id(request)}@test.com"
    # Intentar crear primer admin
    resp = client.post("/api/v1/auth/register-admin", json={
        "nombre": "Admin",
        "apellido": "Hotel",
        "email": email,
        "password": "Admin1234",
    })

    # Si ya existe un admin, creamos uno como cliente y luego lo promovemos
    if resp.status_code != 201:
        client.post("/api/v1/auth/register", json={
            "nombre": "Admin",
            "apellido": "Hotel",
            "email": email,
            "password": "Admin1234",
            "documento_id": "88888888",
            "tipo_documento": "CC"
        })

    resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Admin1234",
    })

    if resp.status_code == 200:
        token = resp.get_json()["data"]["token"]
        # Cambiar el rol a admin directamente en la BD para tests
        with app.app_context():
            user = Usuario.query.filter_by(email=email).first()
            if user:
                user.rol = RolEnum.admin
                db.session.commit()
        return {"Authorization": f"Bearer {token}"}
    return {"Authorization": ""}


class TestListarHabitaciones:

    def test_listar_sin_datos_retorna_lista_vacia(self, client):
        resp = client.get("/api/v1/habitaciones/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["total"] == 0

    def test_listar_con_una_habitacion(self, client, habitacion_en_db):
        resp = client.get("/api/v1/habitaciones/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 1
        assert data["data"][0]["id"] == habitacion_en_db["id"]

    def test_listar_filtro_por_tipo_valido(self, client, habitacion_en_db):
        resp = client.get("/api/v1/habitaciones/?tipo=Simple")
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 1

    def test_listar_filtro_por_tipo_invalido_retorna_400(self, client):
        resp = client.get("/api/v1/habitaciones/?tipo=Inexistente")
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False


class TestObtenerHabitacion:

    def test_obtener_habitacion_existente(self, client, habitacion_en_db):
        hab_id = habitacion_en_db["id"]
        resp = client.get(f"/api/v1/habitaciones/{hab_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == hab_id

    def test_obtener_habitacion_inexistente_retorna_404(self, client):
        resp = client.get("/api/v1/habitaciones/9999")
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False


class TestCrearHabitacion:

    def test_crear_habitacion_como_admin_retorna_201(
        self, client, admin_headers, habitacion_data
    ):
        resp = client.post(
            "/api/v1/habitaciones/",
            json=habitacion_data,
            headers=admin_headers
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["numero"] == "101"
        assert data["data"]["tipo"] == "Simple"

    def test_crear_habitacion_como_cliente_retorna_403(
        self, client, cliente_headers, habitacion_data
    ):
        resp = client.post(
            "/api/v1/habitaciones/",
            json=habitacion_data,
            headers=cliente_headers
        )
        assert resp.status_code == 403

    def test_crear_habitacion_sin_token_retorna_401(
        self, client, habitacion_data
    ):
        resp = client.post("/api/v1/habitaciones/", json=habitacion_data)
        assert resp.status_code == 401

    def test_crear_habitacion_numero_duplicado_retorna_400(
        self, client, admin_headers, habitacion_en_db, habitacion_data
    ):
        habitacion_data["numero"] = habitacion_en_db["numero"]
        resp = client.post(
            "/api/v1/habitaciones/",
            json=habitacion_data,
            headers=admin_headers
        )
        assert resp.status_code == 400
        assert "numero" in resp.get_json()["mensaje"].lower()

    def test_crear_habitacion_tipo_invalido_retorna_400(
        self, client, admin_headers, habitacion_data
    ):
        habitacion_data["tipo"] = "Penthouse"
        resp = client.post(
            "/api/v1/habitaciones/",
            json=habitacion_data,
            headers=admin_headers
        )
        assert resp.status_code == 400

    def test_crear_habitacion_precio_negativo_retorna_400(
        self, client, admin_headers, habitacion_data
    ):
        habitacion_data["precio_noche"] = -5000
        resp = client.post(
            "/api/v1/habitaciones/",
            json=habitacion_data,
            headers=admin_headers
        )
        assert resp.status_code == 400

    def test_crear_habitacion_sin_campos_requeridos_retorna_400(
        self, client, admin_headers
    ):
        resp = client.post(
            "/api/v1/habitaciones/",
            json={"descripcion": "Sin campos obligatorios"},
            headers=admin_headers
        )
        assert resp.status_code == 400


class TestActualizarHabitacion:

    def test_actualizar_precio_como_admin(
        self, client, admin_headers, habitacion_en_db
    ):
        hab_id = habitacion_en_db["id"]
        resp = client.put(
            f"/api/v1/habitaciones/{hab_id}",
            json={"precio_noche": 200000.00},
            headers=admin_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["precio_noche"] == 200000.00

    def test_actualizar_habitacion_inexistente_retorna_404(
        self, client, admin_headers
    ):
        resp = client.put(
            "/api/v1/habitaciones/9999",
            json={"precio_noche": 200000.00},
            headers=admin_headers
        )
        assert resp.status_code == 404

    def test_actualizar_como_cliente_retorna_403(
        self, client, cliente_headers, habitacion_en_db
    ):
        hab_id = habitacion_en_db["id"]
        resp = client.put(
            f"/api/v1/habitaciones/{hab_id}",
            json={"precio_noche": 200000.00},
            headers=cliente_headers
        )
        assert resp.status_code == 403


class TestEliminarHabitacion:

    def test_eliminar_habitacion_como_admin(
        self, client, admin_headers, habitacion_en_db
    ):
        hab_id = habitacion_en_db["id"]
        resp = client.delete(
            f"/api/v1/habitaciones/{hab_id}",
            headers=admin_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        # Soft delete: la habitación existe pero no aparece en listado
        resp2 = client.get("/api/v1/habitaciones/")
        assert resp2.get_json()["total"] == 0

    def test_eliminar_habitacion_inexistente_retorna_404(
        self, client, admin_headers
    ):
        resp = client.delete(
            "/api/v1/habitaciones/9999",
            headers=admin_headers
        )
        assert resp.status_code == 404


class TestBuscarDisponibles:

    def test_disponibles_retorna_habitacion_disponible(
        self, client, habitacion_en_db
    ):
        resp = client.get(
            "/api/v1/habitaciones/disponibles"
            "?fecha_entrada=2027-01-10&fecha_salida=2027-01-15"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"][0]["noches"] == 5
        assert data["data"][0]["total_estimado"] == 750000.00

    def test_disponibles_fecha_entrada_en_pasado_retorna_400(self, client):
        resp = client.get(
            "/api/v1/habitaciones/disponibles"
            "?fecha_entrada=2020-01-01&fecha_salida=2020-01-05"
        )
        assert resp.status_code == 400

    def test_disponibles_fecha_entrada_igual_salida_retorna_400(self, client):
        resp = client.get(
            "/api/v1/habitaciones/disponibles"
            "?fecha_entrada=2027-01-10&fecha_salida=2027-01-10"
        )
        assert resp.status_code == 400

    def test_disponibles_sin_parametros_retorna_400(self, client):
        resp = client.get("/api/v1/habitaciones/disponibles")
        assert resp.status_code == 400

    def test_disponibles_filtro_por_tipo(self, client, habitacion_en_db):
        resp = client.get(
            "/api/v1/habitaciones/disponibles"
            "?fecha_entrada=2027-01-10&fecha_salida=2027-01-15&tipo=Doble"
        )
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0