# HotelBook Pro — Agent Instructions

## Stack & Estructura

- **Flask 3.1** con Application Factory (`create_app()` en `app/__init__.py`)
- **SQLAlchemy 2.0** + Flask-SQLAlchemy 3.1
- **Python 3.12** en CI, desarrollo local también
- Backend API REST en `app/` (controllers, services, models)
- Frontend (HTML/CSS/JS vanilla) en `app/templates/` y `app/static/`
- Tests en `tests/` con pytest + pytest-cov

## Convenios obligatorios (backend)

- Hora Colombia: usar `ahora_colombia()` (nunca `datetime.utcnow()`)
- Enums: `native_enum=False` en modelos
- Respuesta API: `{"success": bool, "data": ..., "error": {...}}` en todos los endpoints
- Errores: `{"success": False, "error": {"code": "CODE", "message": "..."}}`
- Mensajes al usuario en español
- Fecha de Colombia en todos los timestamps

## SQLAlchemy 2.0

- PK lookup: `db.session.get(Model, id)` — nunca `Model.query.get(id)`
- Queries con filtro: `db.session.execute(select(Model).filter_by(...)).scalars().all()`
- `scalar_one_or_none()` para uno o ninguno
- Solo `db.session.query(func.count(), func.sum())` para agregaciones

## Testing

```bash
# Todo
python -m pytest tests/ --cov=app --cov-fail-under=90 -v

# Un archivo
python -m pytest tests/test_auth_extra.py -v

# Con coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```

Fixtures disponibles en `tests/conftest.py`: `app`, `client`, `db`, `cliente`, `admin`, `cliente_headers`
Testing usa SQLite in-memory y `BCRYPT_LOG_ROUNDS=4` (rápido).

## CI/CD

- **Linting**: `flake8 app/ --max-line-length=100 --select=E,F` → 0 errores obligatorios
- **Tests**: `pytest tests/ --cov=app --cov-fail-under=90`
- CI corre en GitHub Actions (`.github/workflows/python-app.yml`)
- Solo branches `main` y `Development` disparan CI

## Archivos & Generación

- **PDF**: generar en memoria con `reportlab`, guardar en `app/static/facturas/`, borrar después de servir
- **Excel**: `openpyxl`, guardar en `app/static/reportes/`, borrar después de servir
- `.env` y `*.env` siempre en `.gitignore` (nunca commitear credenciales)

## Modelo de usuarios y roles

Jerarquía: admin > gerente > recepcionista > cliente

- `AuthService._puede_gestionar_usuario(current_user, usuario)` — maneja permisos
- `AuthService._nivel_rol()` — retorna nivel numérico del rol
- `token_required` y `rol_requerido()` decorators en `jwt_helper.py`
- No se puede editar/desactivar/eliminar el propio usuario

## Rutas de API

- Auth: `/api/v1/auth/*`
- Habitaciones: `/api/v1/habitaciones/*`
- Huespedes: `/api/v1/huespedes/*`
- Reservas: `/api/v1/reservas/*`
- Facturas: `/api/v1/facturas/*`
- Servicios: `/api/v1/servicios/*`
- Pagos: `/api/v1/pagos/*`
- Reportes: `/api/v1/reportes/*`

## Frontend (14 pantallas — IMPLEMENTADAS)

Cliente: Login/Registro → Buscar habitaciones → Detalle habitación → Mis reservas → Detalle reserva + pago
Recepcionista: Dashboard → Lista reservas + acciones → Checkin/Checkout → Agregar servicios → Huéspedes + puntos
Admin/Gerente: Dashboard métricas → Gestión habitaciones → Gestión usuarios → Reportes

### Arquitectura Frontend

- **Templates**: `app/templates/` — organizados por rol (`public/`, `cliente/`, `admin/`, `recepcionista/`, `layouts/`)
- **CSS**: `app/static/css/` — `global.css` + CSS por rol, diseño editorial luxury (Playfair Display + Inter, paleta beige/dorado)
- **JS**: `app/static/js/` — `global.js` (reveal animations + navbar scroll + mobile menu) + JS por rol
- **Base layout**: `app/templates/layouts/base_public.html` — navbar + footer + Google Fonts, SIN inline styles/scripts
- **Blueprint**: `views_bp` registrado en `app/__init__.py` sin prefijo (`url_prefix="/"`)

### Modelo Enum — VALORES LOWERCASE

`TipoHabitacion`: `"simple"`, `"doble"`, `"suite"`, `"deluxe"`
`EstadoHabitacion`: `"disponible"`, `"ocupada"`, `"mantenimiento"`
`EstadoReserva`: `"Pendiente"`, `"Confirmada"`, `"Ocupada"`, `"Completada"`, `"Cancelada"` (sin cambios)
Filtros en templates y API usan valores lowercase para TipoHabitacion y EstadoHabitacion.

## Configuración de BD

- Producción: PostgreSQL (configurar `DATABASE_URL` o `DB_*` en `.env`)
- Desarrollo: SQLite local si no hay `DB_HOST` ni `DATABASE_URL`
- Testing: SQLite en memoria (`create_app("testing")`)

## Known issues

- `DeprecationWarning: datetime.utcnow()` — viene de `openpyxl` internamente, no es código propio, ignorarlo
