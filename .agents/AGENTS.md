# HotelBook Pro — Agent Instructions

## Stack & Estructura

- **Flask 3.1** con Application Factory (`create_app()` en `app/__init__.py`)
- **SQLAlchemy 2.0** + Flask-SQLAlchemy 3.1
- **PostgreSQL** (producción y desarrollo) / SQLite en testing
- **Python 3.12+** en CI y desarrollo local
- **Vue 3** (Composition API, `<script setup>`) + Vite + Tailwind CSS v4
- **Pinia** (estado global), **Vue Router** (SPA routing), **Axios** (HTTP client)
- Backend API REST en `app/` (controllers, services, models)
- Frontend SPA en `frontend/`
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
- Servicios adicionales: registro propio sin prefijo
- Puntos fidelidad: `/api/v1/huespedes` (bajo blueprint de huéspedes)

## Frontend (Vue SPA)

### Estructura

- **Entrada**: `frontend/index.html` → monta Vue en `#app`
- **Código fuente**: `frontend/src/`
- **Build tool**: Vite 8
- **Estilos**: Tailwind CSS v4
- **Gestor de paquetes**: pnpm

### Navegación por roles

- **Cliente**: Login/Registro → Buscar habitaciones → Detalle habitación → Mis reservas → Detalle reserva + pago
- **Recepcionista**: Dashboard → Lista reservas + acciones → Checkin/Checkout → Agregar servicios → Huéspedes + puntos
- **Admin/Gerente**: Dashboard métricas → Gestión habitaciones → Gestión usuarios → Reportes

### Ejecución

```bash
cd frontend
pnpm install
pnpm run dev    # http://localhost:5173
```

## Modelo Enum — VALORES LOWERCASE

`TipoHabitacion`: `"simple"`, `"doble"`, `"suite"`, `"deluxe"`
`EstadoHabitacion`: `"disponible"`, `"ocupada"`, `"mantenimiento"`
`EstadoReserva`: `"Pendiente"`, `"Confirmada"`, `"Ocupada"`, `"Completada"`, `"Cancelada"` (sin cambios)
Filtros en templates y API usan valores lowercase para TipoHabitacion y EstadoHabitacion.

## Configuración de BD

- Producción: PostgreSQL (configurar `DATABASE_URL` o `DB_*` en `.env`)
- Desarrollo: PostgreSQL local (por defecto `localhost:5432`, DB `hotelbook`)
- Testing: SQLite en memoria (`create_app("testing")`)

## Diagrama de datos

El modelo entidad-relación está documentado en `docs/diagram.mmd` (formato Mermaid).
Incluye 11 tablas: usuarios, huéspedes, habitaciones, reservas, checkin_checkout, facturas, pagos, reembolsos, puntos_fidelidad, servicios_adicionales, notificaciones.

## Estrategia de ramas

- `main` — producción estable
- `Development` — integración (rama por defecto del equipo)
- `feature/*` — funcionalidades nuevas
- `Testing` — rama de pruebas

## Convención de commits

Se sigue [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `style:`

## Known issues

- `DeprecationWarning: datetime.utcnow()` — viene de `openpyxl` internamente, no es código propio, ignorarlo
