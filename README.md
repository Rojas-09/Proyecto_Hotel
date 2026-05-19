# HotelBook Pro
> *Solución integral de gestión hotelera para establecimientos medianos con proyección de crecimiento*

**HotelBook Pro** es un sistema de gestión hotelera completo que permite administrar reservas, huéspedes, habitaciones, facturación, check-in, check-out y servicios adicionales. El propósito fundamental es consolidar una plataforma madura, robusta y escalable que resuelva fallos críticos de la gestión manual como el overbooking y las inconsistencias en facturación.

---

## ✨ Características Principales

### Gestión Principal
- ✅ **Gestión de Reservas**: Crear, modificar, cancelar y consultar reservas.
- ✅ **Control de Habitaciones**: Tipos, precios, disponibilidad en tiempo real.
- ✅ **Registro de Huéspedes**: Historial completo y gestión de datos.
- ✅ **Check-in/Check-out**: Proceso digital con comprobantes y flujos automáticos.

### Operaciones Financieras
- ✅ **Facturación Automatizada**: Generación de facturas en PDF con impuestos (19%).
- ✅ **Gestión de Pagos**: Registro de liquidaciones y cargos adicionales.
- ✅ **Garantía de Reserva**: Pago inicial obligatorio para confirmar reservas.

### Servicios Ampliados
- ✅ **Servicios Adicionales**: Cargos por Comedor, Spa, Lavandería, etc., enlazados directamente a la factura de la habitación.
- ✅ **Sistema de Fidelización**: Acumulación automática de puntos por noche.

### Inteligencia de Negocio
- ✅ **Reportes Estratégicos**: Métricas de ocupación e ingresos exportables (Excel, PDF).

---

## 🏗️ Arquitectura y Stack Tecnológico

El proyecto cuenta con una arquitectura en dos capas separadas e independientes:

### Backend (API REST)
Ubicado en el directorio `app/`. Maneja toda la lógica de negocio, autenticación JWT, conexión a la base de datos y validaciones de flujo estrictas.
- **Python 3.12+**
- **Flask** (Framework web)
- **SQLAlchemy 2.0+** (ORM)
- **PyJWT** (Autenticación)
- **SQLite** (Base de datos por defecto `hotelbook_dev.db`)

### Frontend (SPA)
Ubicado en el directorio `frontend/`. Se comunica exclusivamente con el backend a través de endpoints REST.
- **Vue 3** (Composition API, `<script setup>`)
- **Vite** (Motor de construcción rápido)
- **Tailwind CSS v4** (Framework de diseño)
- **Pinia** (Manejo de estado global y sesión)
- **Axios** (Cliente HTTP)

```
┌─────────────────────────────────────────┐
│   CAPA DE PRESENTACIÓN (Frontend Vue 3) │
└────────────────┬────────────────────────┘
                 │ HTTP REST (JSON + JWT)
┌────────────────▼────────────────────────┐
│  CAPA DE LÓGICA DE NEGOCIO (Backend API)│
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   CAPA DE DATOS (SQLite / PostgreSQL)   │
└─────────────────────────────────────────┘
```

---

## 💻 Instalación y Ejecución Local

### 1. Levantar el Backend (API Flask)

Abre una terminal en la raíz del proyecto y ejecuta:

```bash
# Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar las dependencias
pip install -r requirements.txt

# Inicializar y migrar base de datos (Si es la primera vez)
flask db init
flask db migrate
flask db upgrade

# Iniciar la aplicación en modo desarrollo
python run.py
```
> El backend se levantará en **http://127.0.0.1:5000**

### 2. Levantar el Frontend (Vue 3)

Abre **otra pestaña de terminal** y ejecuta:

```bash
cd frontend

# Instalar dependencias de Node.js
npm install

# Iniciar el servidor de desarrollo
npm run dev
```
> El frontend se levantará en **http://localhost:5173** (o el puerto que indique la terminal).

---

## 🔑 Credenciales de Acceso

La base de datos incluye usuarios de prueba para explorar los distintos niveles de acceso:

| Rol | Email | Contraseña | Descripción y Permisos |
|-----|-------|------------|------------------------|
| **Administrador** | `admin@hotel.com` | `admin123` | Acceso total al sistema. Puede crear habitaciones, eliminar, emitir facturas, etc. |
| **Recepcionista** | `recepcionista@hotel.com` | `recep123` | Gestión operativa: reservas, check-in, check-out, servicios, huéspedes. |
| **Gerente** | `gerente@hotel.com` | `gerente123` | Acceso de solo lectura a los Reportes estratégicos (Ocupación e Ingresos). |

---

## 📋 Flujo de Operación (Workflow Principal)

El sistema tiene reglas de negocio estrictas. Para realizar un ciclo completo de estadía de forma exitosa, sigue este flujo usando la cuenta de **Administrador** o **Recepcionista**:

1. **Gestión de Habitaciones:** Ve a "Habitaciones" y crea una nueva habitación.
2. **Gestión de Huéspedes:** Ve a "Huéspedes" y registra a un nuevo cliente.
3. **Creación de Reserva:** Ve a "Reservas" y crea una reserva (nace en estado **Pendiente**).
4. **Confirmación y Pago de Garantía:** En la tabla de Reservas, presiona "Confirmar". Esto procesa el pago inicial y la cambia a **Confirmada**.
5. **Check-In:** Ve a "Recepción" (Check-in). Selecciona la reserva para registrar la llegada. Pasa a estado **Ocupada**.
6. **Servicios Adicionales:** Ve a "Servicios". Agrega cargos por Comedor, Spa, etc.
7. **Check-Out y Liquidación:** Ve a "Recepción" (Check-out). El sistema sumará el saldo de la habitación más los servicios adicionales. Al confirmar, procesa el pago de liquidación y la reserva pasa a **Completada**.
8. **Facturación:** Ve a "Facturación". Emite la factura oficial (PDF).

---

## 🔌 Documentación de la API REST

Todos los endpoints requieren un **JWT (JSON Web Tokens)** válido enviado a través de la cabecera: `Authorization: Bearer <token>`.

### Endpoints Principales

| Categoría | Método | Endpoint | Descripción |
|-----------|--------|----------|-------------|
| **Reservas** | GET | `/api/v1/reservas/` | Listar reservas |
| **Reservas** | POST | `/api/v1/reservas/` | Crear reserva |
| **Habitaciones** | GET | `/api/v1/habitaciones/disponibles` | Consultar disponibilidad |
| **Check-in/out**| PUT | `/api/v1/reservas/{id}/checkin` | Registrar check-in |
| **Check-in/out**| PUT | `/api/v1/reservas/{id}/checkout`| Registrar check-out |
| **Servicios** | GET | `/api/v1/reservas/{id}/servicios` | Listar servicios cargados |
| **Facturación** | POST | `/api/v1/facturas/reserva/{id}/emitir` | Emitir factura PDF |

*Para ver la documentación completa y dinámica de los endpoints, navega a Swagger UI (si está habilitado): `http://127.0.0.1:5000/api/docs`*

---

## 🎨 Diseño y UI

El frontend ha sido diseñado con un estilo moderno, profesional y *premium* (Dark Mode), incluyendo:
- Tonos sobrios (`gray-900`, `gray-800`) con un acento dorado (`#D4AF37`) que transmite exclusividad.
- Micro-animaciones en los botones, tablas y transiciones de estado.
- Interfaz completamente *Responsive*, adaptable a tablets y computadores de escritorio.
- Componentes modulares (`BaseButton`, `BaseTable`, `BaseModal`) para una UI consistente.

### Mockups de Alta Fidelidad
Aquí se presentan los diseños visuales de referencia de la aplicación:

**1. Pantalla de Inicio de Sesión (Login)**
![Mockup Login](docs/images/mockup_login.png)

**2. Panel de Control (Dashboard)**
![Mockup Dashboard](docs/images/mockup_dashboard.png)

**3. Módulo de Reservas**
![Mockup Reservas](docs/images/mockup_reservas.png)

### Prototipos (Wireframes)
Estructura y flujo lógico del sistema previo al diseño final:

**1. Flujo de Usuario Principal (User Flow)**
![Prototipo Flujo](docs/images/prototype_flow.png)

**2. Modal de Creación de Reserva**
![Prototipo Modal](docs/images/prototype_modal.png)

---
*Desarrollado para HotelBook Pro*
