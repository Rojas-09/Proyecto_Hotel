import pytest

from app import db
from app.models.usuario import Usuario, RolEnum
from app.models.huesped import Huesped
from app.services import huesped_service


def test_huesped_obtener_errores_y_buscar(app):
    with app.app_context():
        db.session.query(Huesped).delete()
        db.session.query(Usuario).delete()
        db.session.commit()

        # obtener_por_id inexistente
        with pytest.raises(LookupError):
            huesped_service.obtener_por_id(99999)

        # obtener_por_usuario inexistente
        with pytest.raises(LookupError):
            huesped_service.obtener_por_usuario(99999)

        # actualizar inexistente
        with pytest.raises(LookupError):
            huesped_service.actualizar(99999, {"documento_id": "123"})

        # buscar sin termino
        with pytest.raises(ValueError):
            huesped_service.buscar("")

        # crear datos y buscar exitoso
        u = Usuario(
            nombre="Bus", apellido="Test", email="bus@test", rol=RolEnum.cliente
        )
        u.password = "Pass1234"
        db.session.add(u)
        db.session.flush()
        h = Huesped(id_usuario=u.id, documento_id="5555", tipo_documento="CC")
        db.session.add(h)
        db.session.commit()

    res = huesped_service.buscar("bus")
    assert isinstance(res, list)
    assert res and res[0]["documento_id"] == "5555"
