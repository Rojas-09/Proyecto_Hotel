"""
Tests - Módulo Huéspedes
Cubre: obtener_todos, obtener_por_id, buscar, actualizar
"""

from tests.conftest import _extract_token_from_cookies
from app.models.usuario import Usuario, RolEnum
from app.models.huesped import Huesped


def obtener_token_admin(client, db):
    """Crea un admin y retorna su token."""
    u = Usuario(
        nombre="Admin",
        apellido="Test",
        email="admin@huespedes.test",
        rol=RolEnum.admin
    )
    u.password = "AdminPass123"
    db.session.add(u)
    db.session.commit()

    res = client.post("/api/v1/auth/login", json={
        "email": "admin@huespedes.test",
        "password": "AdminPass123"
    })
    return _extract_token_from_cookies(client)


class TestObtenerTodos:

    def test_obtener_todos_sin_huespedes(self, client, app, db):
        """Obtener lista vacía si no hay huéspedes."""
        token = obtener_token_admin(client, db)
        res = client.get(
            "/api/v1/huespedes/",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = res.get_json()
        assert res.status_code == 200
        assert data["success"] is True
        assert data["total"] == 0
        assert data["data"] == []

    def test_obtener_todos_con_huespedes(self, client, app, db):
        """Obtener lista con huéspedes."""
        with app.app_context():
            u1 = Usuario(
                nombre="Carlos",
                apellido="Mendoza",
                email="carlos@test.com",
                rol="cliente"
            )
            u1.password = "Pass1234"
            db.session.add(u1)
            db.session.flush()

            h1 = Huesped(
                id_usuario=u1.id,
                documento_id="99999999",
                tipo_documento="CC"
            )
            db.session.add(h1)
            db.session.commit()

        token = obtener_token_admin(client, db)
        res = client.get(
            "/api/v1/huespedes/",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = res.get_json()
        assert res.status_code == 200
        assert data["total"] == 1
        assert data["data"][0]["documento_id"] == "99999999"


class TestObtenerPorId:

    def test_obtener_huesped_existente(self, client, app, db):
        """Obtener un huésped específico."""
        with app.app_context():
            u = Usuario(
                nombre="Pedro",
                apellido="López",
                email="pedro@test.com",
                rol="cliente"
            )
            u.password = "Pass1234"
            db.session.add(u)
            db.session.flush()

            h = Huesped(
                id_usuario=u.id,
                documento_id="77777777",
                tipo_documento="CC",
                preferencias="Piso alto"
            )
            db.session.add(h)
            db.session.commit()
            huesped_id = h.id

        token = obtener_token_admin(client, db)
        res = client.get(
            f"/api/v1/huespedes/{huesped_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = res.get_json()
        assert res.status_code == 200
        assert data["success"] is True
        assert data["data"]["documento_id"] == "77777777"

    def test_obtener_huesped_inexistente(self, client, db):
        """Obtener huésped que no existe."""
        token = obtener_token_admin(client, db)
        res = client.get(
            "/api/v1/huespedes/999",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 404


class TestBuscar:

    def test_buscar_por_nombre(self, client, app, db):
        """Buscar huésped por nombre."""
        with app.app_context():
            u = Usuario(
                nombre="Roberto",
                apellido="García",
                email="roberto@test.com",
                rol="cliente"
            )
            u.password = "Pass1234"
            db.session.add(u)
            db.session.flush()

            h = Huesped(
                id_usuario=u.id,
                documento_id="55555555",
                tipo_documento="CC"
            )
            db.session.add(h)
            db.session.commit()

        token = obtener_token_admin(client, db)
        res = client.get(
            "/api/v1/huespedes/buscar?q=Roberto",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = res.get_json()
        assert res.status_code == 200
        assert data["total"] == 1
        assert "Roberto" in data["data"][0]["nombre"]

    def test_buscar_por_documento(self, client, app, db):
        """Buscar huésped por documento_id."""
        with app.app_context():
            u = Usuario(
                nombre="Marta",
                apellido="Ruiz",
                email="marta@test.com",
                rol="cliente"
            )
            u.password = "Pass1234"
            db.session.add(u)
            db.session.flush()

            h = Huesped(
                id_usuario=u.id,
                documento_id="88888888",
                tipo_documento="CC"
            )
            db.session.add(h)
            db.session.commit()

        token = obtener_token_admin(client, db)
        res = client.get(
            "/api/v1/huespedes/buscar?q=88888888",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = res.get_json()
        assert res.status_code == 200
        assert data["total"] == 1

    def test_buscar_sin_resultados(self, client, db):
        """Buscar sin resultados."""
        token = obtener_token_admin(client, db)
        res = client.get(
            "/api/v1/huespedes/buscar?q=NoExiste",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = res.get_json()
        assert res.status_code == 200
        assert data["total"] == 0

    def test_buscar_sin_parametro_q(self, client, db):
        """Buscar sin parámetro q."""
        token = obtener_token_admin(client, db)
        res = client.get(
            "/api/v1/huespedes/buscar",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 400


class TestActualizar:

    def test_actualizar_documento_id(self, client, app, db):
        """Actualizar documento_id."""
        with app.app_context():
            u = Usuario(
                nombre="Lucia",
                apellido="Fernández",
                email="lucia@test.com",
                rol="cliente"
            )
            u.password = "Pass1234"
            db.session.add(u)
            db.session.flush()

            h = Huesped(
                id_usuario=u.id,
                documento_id="66666666",
                tipo_documento="CC"
            )
            db.session.add(h)
            db.session.commit()
            huesped_id = h.id

        token = obtener_token_admin(client, db)
        res = client.put(
            f"/api/v1/huespedes/{huesped_id}",
            json={"documento_id": "11111111"},
            headers={"Authorization": f"Bearer {token}"}
        )
        data = res.get_json()
        assert res.status_code == 200
        assert data["data"]["documento_id"] == "11111111"

    def test_actualizar_preferencias(self, client, app, db):
        """Actualizar preferencias."""
        with app.app_context():
            u = Usuario(
                nombre="Diego",
                apellido="Sánchez",
                email="diego@test.com",
                rol="cliente"
            )
            u.password = "Pass1234"
            db.session.add(u)
            db.session.flush()

            h = Huesped(
                id_usuario=u.id,
                documento_id="44444444",
                tipo_documento="CC",
                preferencias="Sin preferencias"
            )
            db.session.add(h)
            db.session.commit()
            huesped_id = h.id

        token = obtener_token_admin(client, db)
        res = client.put(
            f"/api/v1/huespedes/{huesped_id}",
            json={"preferencias": "Piso bajo, cerca del ascensor"},
            headers={"Authorization": f"Bearer {token}"}
        )
        data = res.get_json()
        assert res.status_code == 200
        assert "Piso bajo" in data["data"]["preferencias"]
