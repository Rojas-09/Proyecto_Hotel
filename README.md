# HotelBook Pro

> *Solución integral de gestión hotelera para establecimientos medianos con proyección de crecimiento.*

**HotelBook Pro** es una plataforma centralizada (SPA + API REST) diseñada para resolver la gestión operativa diaria de un hotel de tamaño medio. El proyecto soluciona problemas críticos como el overbooking, la inconsistencia en facturación y los tiempos prolongados de respuesta. Integra de forma cohesiva la gestión de habitaciones, control de reservas, sistema de huéspedes, facturación, reportes estratégicos y servicios adicionales (Spa y Comedor).

---

## 🛠️ Stack Tecnológico

**Backend:**
- Python 3.12
- Flask 3.1.3 (API REST)
- SQLAlchemy 2.0+ (ORM)
- PostgreSQL 12+ (Producción) / SQLite (Desarrollo)

**Frontend:**
- Vue 3 + Vite
- Vue Router 4 (Navegación protegida)
- Pinia (Gestión del estado global)
- Tailwind CSS v4 (Diseño responsivo y utilidades)
- Axios (Cliente HTTP)

---

## 📋 Requisitos Previos

Asegúrate de contar con las siguientes herramientas instaladas:
- **Node.js** (v18 o superior) y npm
- **Python** (3.11+)
- **Git**

---

## 🚀 Instrucciones de Instalación

Sigue estos pasos para levantar el proyecto de forma local:

### 1. Clonar el repositorio
```bash
git clone https://github.com/paulmopl2025/Proyecto_Hotel.git
cd Proyecto_Hotel
```

### 2. Configurar el Backend (Flask)
```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Inicializar y migrar base de datos local
flask db init
flask db migrate
flask db upgrade
```

### 3. Configurar el Frontend (Vue 3)
```bash
# 1. Entrar a la carpeta frontend
cd frontend

# 2. Instalar dependencias de Node
npm install
```

### 4. Variables de Entorno (Local)
Backend (`/Proyecto_Hotel/.env`):
```env
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY=clave_segura
JWT_EXPIRATION_HOURS=24
PORT=5000
```
Frontend (`/Proyecto_Hotel/frontend/.env`):
```env
VITE_API_URL=http://127.0.0.1:5000/api/v1
```

---

## ▶️ Cómo correr el proyecto en local

Debes mantener dos terminales abiertas:

**Terminal 1: Backend**
```bash
cd Proyecto_Hotel
source venv/bin/activate
python run.py
# El servidor correrá en: http://127.0.0.1:5000
```

**Terminal 2: Frontend**
```bash
cd Proyecto_Hotel/frontend
npm run dev
# La aplicación correrá en: http://localhost:5173
```

Abre tu navegador en `http://localhost:5173` y verás la pantalla de Login.

---

## 📁 Estructura de Carpetas

```text
Proyecto_Hotel/
├── app/                      # Backend: Lógica de la API REST en Flask
│   ├── models/               # Modelos de base de datos SQLAlchemy
│   ├── controllers/          # Endpoints y Rutas (Blueprint)
│   ├── services/             # Lógica de negocio (Reservas, Facturas)
│   └── ...
├── frontend/                 # Frontend: Aplicación Vue 3 SPA
│   ├── src/
│   │   ├── components/       # Componentes reutilizables (BaseButton, BaseTable)
│   │   ├── layouts/          # Layout principal (MainLayout con Sidebar)
│   │   ├── router/           # Configuración de Vue Router (guards)
│   │   ├── services/         # Configuración de Axios para peticiones HTTP
│   │   ├── stores/           # Pinia store para autenticación
│   │   └── views/            # Vistas principales (Login, Reservas, Habitaciones)
│   ├── .env                  # Variables de entorno de Vite
│   ├── package.json          # Dependencias de npm
│   └── vite.config.js        # Configuración del servidor Vite
├── tests/                    # Pruebas automatizadas backend
├── requirements.txt          # Dependencias de Python
└── README.md                 # Documentación del proyecto
```

---

## 🔌 Endpoints Principales de la API

Todos los endpoints (salvo el Login) requieren el token JWT en las cabeceras: `Authorization: Bearer <token>`

| Módulo | Endpoint | Método | Descripción | Ejemplo de Body |
|--------|----------|--------|-------------|-----------------|
| **Auth** | `/api/v1/auth/login` | POST | Iniciar sesión | `{"email":"admin@hotel.com", "password":"123"}` |
| **Habitaciones**| `/api/v1/habitaciones` | GET | Listar habitaciones | - |
| **Reservas**| `/api/v1/reservas` | POST | Crear reserva | `{"habitacion_id":1, "usuario_id":2, "fecha_entrada":"2026-05-15", ...}`|
| **Facturación**| `/api/v1/facturas` | POST | Generar factura PDF | `{"reserva_id": 5}` |
| **Servicios**| `/api/v1/comedor/pedidos` | POST | Añadir pedido de comedor | `{"reserva_id": 3, "descripcion": "Cena", "total": 50000}`|

---

## 👥 Roles y Permisos

El sistema cuenta con un sistema robusto de acceso por roles:

- **Administrador (`admin`)**: Acceso total al sistema. Puede configurar parámetros, gestionar a todos los usuarios, crear habitaciones y ver reportes.
- **Recepcionista (`recepcionista`)**: Perfil transaccional. Encargado de verificar disponibilidad, crear reservas, hacer check-in/check-out y generar facturas. No tiene acceso a reportes financieros.
- **Gerente (`gerente`)**: Perfil gerencial. Puede acceder a los módulos de reportes estratégicos (Ocupación e Ingresos) y exportar los datos (Excel y PDF).
- **Cliente (`cliente`)**: Perfil limitado. Historial de reservas y puntos de fidelización (uso mayormente pasivo vía API pública).

---

## 🔐 Credenciales de Prueba

Para probar el flujo del sistema de manera local, puedes usar estas cuentas precargadas en el Login:

| Rol | Correo electrónico | Contraseña |
|-----|--------------------|------------|
| **Administrador** | `admin@hotel.com` | `admin123` |
| **Recepcionista** | `recepcionista@hotel.com` | `recep123` |
| **Gerente** | `gerente@hotel.com` | `gerente123` |

---

## 🔄 Flujo de Trabajo Git

Para contribuir al desarrollo, se utiliza un sistema estricto de control de versiones y ramas:

1. **Ramas**: No se trabaja directamente sobre `main` o `develop`. Cada funcionalidad se desarrolla en ramas separadas (ej. `feature/frontend-vue`, `fix/login-bug`).
2. **Commits Atómicos**: Se usa Conventional Commits para registrar cambios:
   - `feat: agregar vista de reservas`
   - `fix: corregir cálculo de IVA en facturas`
   - `docs: actualizar readme de instalación`
3. **Pull Requests (PR)**: Se fusionan los cambios mediante PR a `develop` solicitando revisión de código.

---

## 🧑‍💻 Autores

- **Backend**: Rojas-09 ([GitHub Profile](https://github.com/Rojas-09))
- **Frontend**: paulmopl2025 ([GitHub Profile](https://github.com/paulmopl2025))

---

## 📞 Contacto

**Email Soporte**: [sistemahotelbook@gmail.com](mailto:sistemahotelbook@gmail.com)
