from tests.conftest import _extract_token_from_cookies
from app import db
from app.models.usuario import Usuario
from app.services.auth_service import AuthService


def _crear_usuario(nombre, apellido, email, rol, password):
    u = Usuario(nombre=nombre, apellido=apellido, email=email, rol=rol)
    u.password = password
    db.session.add(u)
    db.session.commit()
    return u


def test_crear_primer_admin_exitoso(app):
    with app.app_context():
        data = {
            "nombre": "Root",
            "apellido": "Admin",
            "email": "root@test.com",
            "password": "Admin1234",
        }
        result, status, *_ = AuthService.crear_primer_admin(data)
        assert status == 201
        assert result["success"] is True
        assert result["data"]["usuario"]["rol"] == "admin"


def test_crear_primer_admin_falla_si_ya_existe_admin(app):
    with app.app_context():
        _crear_usuario("A", "B", "admin@test.com", "admin", "Admin1234")
        result, status = AuthService.crear_primer_admin(
            {
                "nombre": "Otro",
                "apellido": "Admin",
                "email": "otro@test.com",
                "password": "Admin1234",
            }
        )
        assert status == 403
        assert result["error"]["code"] == "FORBIDDEN"


def test_crear_primer_admin_valida_campos_requeridos(app):
    with app.app_context():
        result, status = AuthService.crear_primer_admin(
            {
                "nombre": "SinApellido",
                "email": "x@test.com",
                "password": "Admin1234",
            }
        )
        assert status == 400
        assert result["error"]["code"] == "VALIDATION_ERROR"


def test_crear_primer_admin_password_corta(app):
    with app.app_context():
        result, status = AuthService.crear_primer_admin(
            {
                "nombre": "N",
                "apellido": "A",
                "email": "x2@test.com",
                "password": "123",
            }
        )
        assert status == 400
        assert result["error"]["code"] == "VALIDATION_ERROR"


def test_crear_usuario_admin_rol_invalido(app):
    with app.app_context():
        result, status = AuthService.crear_usuario_admin(
            {
                "nombre": "X",
                "apellido": "Y",
                "email": "xy@test.com",
                "password": "Password123",
                "rol": "superadmin",
            }
        )
        assert status == 400
        assert result["error"]["code"] == "VALIDATION_ERROR"


def test_editar_mi_perfil_rechaza_email(app):
    with app.app_context():
        user = _crear_usuario("Ana", "Uno", "ana1@test.com", "cliente", "Password123")
        result, status = AuthService.editar_mi_perfil(user, {"email": "nuevo@test.com"})
        assert status == 400
        assert result["error"]["code"] == "VALIDATION_ERROR"


def test_editar_mi_perfil_rechaza_rol(app):
    with app.app_context():
        user = _crear_usuario("Ana", "Dos", "ana2@test.com", "cliente", "Password123")
        result, status = AuthService.editar_mi_perfil(user, {"rol": "admin"})
        assert status == 400
        assert result["error"]["code"] == "FORBIDDEN"


def test_editar_mi_perfil_rechaza_password_corta(app):
    with app.app_context():
        user = _crear_usuario("Ana", "Tres", "ana3@test.com", "cliente", "Password123")
        result, status = AuthService.editar_mi_perfil(user, {"password": "123"})
        assert status == 400
        assert result["error"]["code"] == "VALIDATION_ERROR"


def test_editar_mi_perfil_rechaza_cambiar_activo(app):
    with app.app_context():
        user = _crear_usuario(
            "Ana", "Cuatro", "ana4@test.com", "cliente", "Password123"
        )
        result, status = AuthService.editar_mi_perfil(user, {"activo": False})
        assert status == 400
        assert result["error"]["code"] == "FORBIDDEN"


def test_editar_mi_perfil_actualiza_campos(app):
    with app.app_context():
        user = _crear_usuario("Ana", "Cinco", "ana5@test.com", "cliente", "Password123")
        result, status = AuthService.editar_mi_perfil(
            user,
            {
                "nombre": "Ana Maria",
                "apellido": "Cinco Dos",
                "telefono": " 3001234567 ",
                "password": "NuevaPass123",
            },
        )
        assert status == 200
        assert result["success"] is True
        assert user.nombre == "Ana Maria"
        assert user.apellido == "Cinco Dos"
        assert user.telefono == "3001234567"


def test_editar_usuario_no_encontrado(app):
    with app.app_context():
        admin = _crear_usuario("Admin", "One", "admin1@test.com", "admin", "Admin1234")
        result, status = AuthService.editar_usuario(9999, admin, {"nombre": "X"})
        assert status == 404
        assert result["error"]["code"] == "NOT_FOUND"


def test_editar_usuario_cliente_sin_permiso(app):
    with app.app_context():
        cliente = _crear_usuario("Cli", "A", "cli1@test.com", "cliente", "Password123")
        otro = _crear_usuario("Otro", "B", "otro1@test.com", "cliente", "Password123")
        result, status = AuthService.editar_usuario(otro.id, cliente, {"nombre": "No"})
        assert status == 403
        assert result["error"]["code"] == "FORBIDDEN"


def test_editar_usuario_gerente_no_puede_editar_admin(app):
    with app.app_context():
        gerente = _crear_usuario(
            "Ger", "Uno", "ger1@test.com", "gerente", "Password123"
        )
        admin = _crear_usuario("Adm", "Uno", "adm1@test.com", "admin", "Password123")
        result, status = AuthService.editar_usuario(admin.id, gerente, {"nombre": "No"})
        assert status == 403
        assert result["error"]["code"] == "FORBIDDEN"


def test_editar_usuario_no_puede_desactivarse_a_si_mismo(app):
    with app.app_context():
        admin = _crear_usuario("Admin", "Self", "self@test.com", "admin", "Password123")
        result, status = AuthService.editar_usuario(admin.id, admin, {"activo": False})
        assert status == 403
        assert result["error"]["code"] == "FORBIDDEN"


def test_editar_usuario_no_puede_cambiar_su_rol(app):
    with app.app_context():
        gerente = _crear_usuario(
            "Ger", "Self", "gerself@test.com", "gerente", "Password123"
        )
        result, status = AuthService.editar_usuario(
            gerente.id, gerente, {"rol": "admin"}
        )
        assert status == 403
        assert result["error"]["code"] == "FORBIDDEN"


def test_editar_usuario_solo_admin_cambia_email(app):
    with app.app_context():
        gerente = _crear_usuario(
            "Ger", "Dos", "ger2@test.com", "gerente", "Password123"
        )
        recep = _crear_usuario(
            "Rec", "Dos", "rec2@test.com", "recepcionista", "Password123"
        )
        result, status = AuthService.editar_usuario(
            recep.id, gerente, {"email": "nuevo@test.com"}
        )
        assert status == 403
        assert result["error"]["code"] == "FORBIDDEN"


def test_editar_usuario_email_conflicto(app):
    with app.app_context():
        admin = _crear_usuario(
            "Admin", "Dos", "admin2@test.com", "admin", "Password123"
        )
        u1 = _crear_usuario("U1", "A", "u1@test.com", "cliente", "Password123")
        _crear_usuario("U2", "B", "u2@test.com", "cliente", "Password123")
        result, status = AuthService.editar_usuario(
            u1.id, admin, {"email": "u2@test.com"}
        )
        assert status == 409
        assert result["error"]["code"] == "CONFLICT"


def test_editar_usuario_rol_invalido(app):
    with app.app_context():
        admin = _crear_usuario(
            "Admin", "Tres", "admin3@test.com", "admin", "Password123"
        )
        u1 = _crear_usuario("U3", "A", "u3@test.com", "cliente", "Password123")
        result, status = AuthService.editar_usuario(u1.id, admin, {"rol": "super"})
        assert status == 400
        assert result["error"]["code"] == "VALIDATION_ERROR"


def test_editar_usuario_gerente_no_asigna_rol_admin(app):
    with app.app_context():
        gerente = _crear_usuario(
            "Ger", "Tres", "ger3@test.com", "gerente", "Password123"
        )
        recep = _crear_usuario(
            "Rec", "Tres", "rec3@test.com", "recepcionista", "Password123"
        )
        result, status = AuthService.editar_usuario(recep.id, gerente, {"rol": "admin"})
        assert status == 403
        assert result["error"]["code"] == "FORBIDDEN"


def test_editar_usuario_solo_admin_activa_desactiva(app):
    with app.app_context():
        gerente = _crear_usuario(
            "Ger", "Cuatro", "ger4@test.com", "gerente", "Password123"
        )
        recep = _crear_usuario(
            "Rec", "Cuatro", "rec4@test.com", "recepcionista", "Password123"
        )
        result, status = AuthService.editar_usuario(
            recep.id, gerente, {"activo": False}
        )
        assert status == 403
        assert result["error"]["code"] == "FORBIDDEN"


def test_editar_usuario_password_corta(app):
    with app.app_context():
        admin = _crear_usuario(
            "Admin", "Cuatro", "admin4@test.com", "admin", "Password123"
        )
        recep = _crear_usuario(
            "Rec", "Cinco", "rec5@test.com", "recepcionista", "Password123"
        )
        result, status = AuthService.editar_usuario(
            recep.id, admin, {"password": "123"}
        )
        assert status == 400
        assert result["error"]["code"] == "VALIDATION_ERROR"


def test_editar_usuario_admin_exitoso(app):
    with app.app_context():
        admin = _crear_usuario(
            "Admin", "Cinco", "admin5@test.com", "admin", "Password123"
        )
        user = _crear_usuario("U5", "A", "u5@test.com", "cliente", "Password123")
        result, status = AuthService.editar_usuario(
            user.id,
            admin,
            {
                "nombre": "Nuevo",
                "apellido": "Nombre",
                "telefono": " 3110000000 ",
                "email": "u5new@test.com",
                "rol": "recepcionista",
                "activo": True,
                "password": "Password999",
            },
        )
        assert status == 200
        assert result["success"] is True
        assert user.email == "u5new@test.com"
        assert user.rol.value == "recepcionista"


def test_auth_controller_me_put_body_requerido(client, app):
    with app.app_context():
        _crear_usuario("Me", "User", "me@test.com", "cliente", "Password123")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "me@test.com", "password": "Password123"},
    )
    token = _extract_token_from_cookies(client)
    resp = client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_auth_controller_usuarios_put_body_requerido(client, app):
    with app.app_context():
        admin = _crear_usuario(
            "Adm", "Ctrl", "admctrl@test.com", "admin", "Password123"
        )
        target = _crear_usuario(
            "Tar", "Get", "target@test.com", "cliente", "Password123"
        )
        _ = target.id
        _ = admin.id
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admctrl@test.com", "password": "Password123"},
    )
    token = _extract_token_from_cookies(client)
    resp = client.put(
        "/api/v1/auth/usuarios/2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_auth_controller_listar_usuarios_y_eliminar(client, app):
    with app.app_context():
        admin = _crear_usuario(
            "Adm", "List", "admlist@test.com", "admin", "Password123"
        )
        user = _crear_usuario(
            "Usr", "List", "usrlist@test.com", "cliente", "Password123"
        )
        user_id = user.id
        admin_id = admin.id
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admlist@test.com", "password": "Password123"},
    )
    token = _extract_token_from_cookies(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp_list = client.get("/api/v1/auth/usuarios", headers=headers)
    assert resp_list.status_code == 200
    assert resp_list.get_json()["total"] >= 2

    resp_self = client.delete(f"/api/v1/auth/usuarios/{admin_id}", headers=headers)
    assert resp_self.status_code == 403

    resp_ok = client.delete(f"/api/v1/auth/usuarios/{user_id}", headers=headers)
    assert resp_ok.status_code == 200

    resp_nf = client.delete("/api/v1/auth/usuarios/9999", headers=headers)
    assert resp_nf.status_code == 404
