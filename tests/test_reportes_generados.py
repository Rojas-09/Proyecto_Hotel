"""
Tests del módulo ReporteGenerado + listar_historial
"""

import pytest
from datetime import date, datetime

from app import db
from app.models.usuario import Usuario, RolEnum
from app.models.reporte import ReporteGenerado
from app.services import reporte_service


# -- helpers --------------------------------------------------------------

def _crear_admin(app, seed: str) -> Usuario:
    u = Usuario(
        nombre="Admin",
        apellido=f"T6-{seed}",
        email=f"t6_admin_{seed}@test.com",
        telefono=f"300{seed[:7]:0>7}",
        rol=RolEnum.admin,
    )
    u.password = "pass123456"
    db.session.add(u)
    return u


def _crear_reporte(admin: Usuario, **kw) -> ReporteGenerado:
    r = ReporteGenerado(
        tipo=kw.get("tipo", "ocupacion"),
        formato=kw.get("formato", "xlsx"),
        fecha_inicio=kw.get("fecha_inicio", date(2026, 1, 1)),
        fecha_fin=kw.get("fecha_fin", date(2026, 1, 31)),
        archivo_path=kw.get("archivo_path", "/tmp/reportes/test.xlsx"),
        archivo_nombre=kw.get("archivo_nombre", "test.xlsx"),
        creado_por=admin.id,
        resumen=kw.get("resumen"),
    )
    db.session.add(r)
    return r


# -- TestReporteGeneradoModel ---------------------------------------------

class TestReporteGeneradoModel:
    def test_crear_registro(self, app):
        with app.app_context():
            admin = _crear_admin(app, "mod1")
            db.session.commit()
            r = _crear_reporte(admin, tipo="ingresos")
            db.session.commit()
            rid = r.id
            db.session.expire_all()
            guardado = db.session.get(ReporteGenerado, rid)
            assert guardado is not None
            assert guardado.tipo == "ingresos"
            assert guardado.formato == "xlsx"
            assert guardado.creado_por == admin.id

    def test_to_dict_serialization(self, app):
        with app.app_context():
            admin = _crear_admin(app, "mod2")
            db.session.commit()
            r = _crear_reporte(
                admin,
                tipo="estadisticas",
                formato="pdf",
                resumen={"total_reservas": 42, "ingresos": 15_000_000},
            )
            db.session.commit()
            d = r.to_dict()
            assert d["tipo"] == "estadisticas"
            assert d["formato"] == "pdf"
            assert d["creado_por"] == admin.id
            assert d["resumen"]["total_reservas"] == 42
            assert d["fecha_inicio"] is not None
            assert d["fecha_fin"] is not None
            assert d["created_at"] is not None

    def test_repr(self, app):
        with app.app_context():
            admin = _crear_admin(app, "mod4")
            db.session.commit()
            r = _crear_reporte(admin, tipo="ocupacion")
            db.session.commit()
            assert "ReporteGenerado" in repr(r)
            assert r.tipo in repr(r)


# -- TestListarHistorial --------------------------------------------------

class TestListarHistorial:
    def test_listar_todos(self, app):
        with app.app_context():
            admin = _crear_admin(app, "hist1")
            db.session.commit()
            _crear_reporte(admin)
            _crear_reporte(admin, tipo="ingresos")
            db.session.commit()
            resultados = reporte_service.listar_historial()
            assert len(resultados) >= 2

    def test_filtrar_por_tipo(self, app):
        with app.app_context():
            admin = _crear_admin(app, "hist2")
            db.session.commit()
            _crear_reporte(admin, tipo="ocupacion")
            _crear_reporte(admin, tipo="ingresos")
            db.session.commit()
            resultados = reporte_service.listar_historial({"tipo": "ocupacion"})
            assert len(resultados) == 1
            assert resultados[0]["tipo"] == "ocupacion"

    def test_filtrar_por_creado_por(self, app):
        with app.app_context():
            admin = _crear_admin(app, "hist3")
            otro = _crear_admin(app, "hist3b")
            db.session.commit()
            _crear_reporte(admin, tipo="ocupacion")
            _crear_reporte(otro, tipo="ingresos")
            db.session.commit()
            resultados = reporte_service.listar_historial({"creado_por": admin.id})
            assert len(resultados) == 1
            assert resultados[0]["creado_por"] == admin.id

    def test_filtrar_por_fecha_desde(self, app):
        with app.app_context():
            admin = _crear_admin(app, "hist4")
            db.session.commit()
            r1 = _crear_reporte(admin, tipo="a")
            r2 = _crear_reporte(admin, tipo="b")
            db.session.commit()
            resultados = reporte_service.listar_historial(
                {"fecha_desde": date.today().isoformat()}
            )
            ids = [r["id"] for r in resultados]
            assert r1.id in ids
            assert r2.id in ids

    def test_filtrar_por_fecha_hasta(self, app):
        with app.app_context():
            admin = _crear_admin(app, "hist5")
            db.session.commit()
            r = _crear_reporte(admin, tipo="vacio")
            db.session.commit()
            resultados = reporte_service.listar_historial(
                {"fecha_hasta": "2025-01-01"}
            )
            assert len(resultados) == 0

    def test_filtrar_por_formato(self, app):
        with app.app_context():
            admin = _crear_admin(app, "hist6")
            db.session.commit()
            _crear_reporte(admin, tipo="ocupacion", formato="xlsx")
            _crear_reporte(admin, tipo="ingresos", formato="pdf")
            db.session.commit()
            resultados = reporte_service.listar_historial({"formato": "pdf"})
            assert len(resultados) == 1
            assert resultados[0]["formato"] == "pdf"

    def test_filtros_vacios_retorna_todos(self, app):
        with app.app_context():
            admin = _crear_admin(app, "hist7")
            db.session.commit()
            _crear_reporte(admin)
            _crear_reporte(admin, tipo="ingresos")
            db.session.commit()
            resultados = reporte_service.listar_historial({})
            assert len(resultados) == 2
