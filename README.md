# HotelBook Pro
> *Solución integral de gestión hotelera para establecimientos medianos con proyección de crecimiento*

**Versión:** 1.0.0 | **Estado:** En Desarrollo 

---

## 📋 Tabla de Contenidos
## 📋 Tabla de Contenidos
- [Descripción](#descripcion)
- [Características](#caracteristicas)
- [Stack Tecnológico](#stack-tecnologico)
- [Arquitectura](#arquitectura)
- [Instalación](#instalacion)
- [Uso](#uso)
- [Roles y Permisos](#roles-y-permisos)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [API REST](#api-rest)
- [Testing y CI/CD](#testing-y-cicd)
- [Hitos de Implementación](#hitos-de-implementacion)
- [Guía de Contribución](#guia-de-contribucion)
- [Licencia](#licencia)
- [Contacto](#contacto)

---

## 🎯 Descripción
## 🎯 Descripción {#descripcion}

**HotelBook Pro** es una solución integral orientada a la transformación digital y centralización operativa de establecimientos hoteleros medianos. El sistema resuelve fallos críticos de la gestión manual como:

- ⚠️ **Overbooking** (doble asignación de habitaciones)
- ⚠️ **Inconsistencia en datos de facturación**
- ⚠️ **Tiempos de respuesta prolongados** en atención al huésped

El propósito fundamental es consolidar una plataforma madura, robusta y escalable que integre:
- Gestión centralizada de reservas
- Servicios adicionales (Comedor, Spa)
- Sistema de fidelización de clientes
- Pasarela de pagos electrónicos

---

## ✨ Características
## ✨ Características {#caracteristicas}

### Gestión Principal
- ✅ **Gestión de Reservas**: Crear, modificar, cancelar y consultar reservas
- ✅ **Control de Habitaciones**: Tipos, precios, disponibilidad en tiempo real
- ✅ **Registro de Huéspedes**: Historial completo, preferencias, documentos
- ✅ **Check-in/Check-out**: Proceso digital con comprobantes automáticos

### Operaciones Financieras
- ✅ **Facturación Automatizada**: Generación de facturas en PDF con IVA (19%)
- ✅ **Gestión de Pagos**: Registro de pagos, reembolsos y cargos
- ✅ **Pasarela de Pagos**: Integración con proveedores externos
- ✅ **Garantía de Reserva**: Pago inicial del 50% para confirmar reserva

### Servicios Ampliados
- ✅ **Gestor de Comedor**: Registro de pedidos vinculados a reservas
- ✅ **Gestor de Spa**: Agenda de citas con validación de traslapes horarios
- ✅ **Sistema de Fidelización**: Acumulación automática de puntos (10/noche)

### Inteligencia de Negocio
- ✅ **Reportes Estratégicos**: Ocupación, ingresos, estadísticas (Excel, PDF)
- ✅ **Notificaciones**: Confirmaciones de reserva por correo automático
- ✅ **Análisis de Desempeño**: Métricas institucionales en tiempo real

---

## 🛠️ Stack Tecnológico
## 🛠️ Stack Tecnológico {#stack-tecnologico}

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| **Backend** | Flask | 3.0+ |
| **Lenguaje** | Python | 3.11+ |
| **ORM** | SQLAlchemy | - |
| **BD (Producción)** | PostgreSQL | 12+ |
| **BD (Desarrollo)** | SQLite | - |
| **API Doc** | Swagger/OpenAPI | - |
| **IDE Recomendado** | Visual Studio Code | - |
| **Extensiones** | Pylance, Python Debugger | - |

---

## 🏗️ Arquitectura
## 🏗️ Arquitectura {#arquitectura}

### Modelo: Arquitectura Monolítica Modular

```
┌─────────────────────────────────────────┐
│   CAPA DE PRESENTACIÓN (Frontend)       │
│  HTML5 | CSS3 | JavaScript Vanilla      │
└────────────────┬────────────────────────┘
                 │ HTTP REST (JSON)
┌────────────────▼────────────────────────┐
│  CAPA DE LÓGICA DE NEGOCIO (Módulos)    │
│  ┌──────────────────────────────────┐   │
│  │ Módulo Reservas      │ Modelos   │   │
│  │ Módulo Habitaciones  │ Servicios │   │
│  │ Módulo Facturación   │ Controladores │
│  │ Módulo Sp/Comedor    │ (Endpoints)   │
│  │ Módulo Fidelización  │           │   │
│  └──────────────────────────────────┘   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   CAPA DE DATOS (Persistencia)          │
│  PostgreSQL (Producción)                │
│  SQLite (Desarrollo/Testing)            │
└─────────────────────────────────────────┘
```

**Ventajas del enfoque modular:**
- 💰 Costo operacional mínimo (USD 5-10/mes por servidor VPS)
- 🚀 Despliegue simple con un único comando (`git push`)
- 🔍 Depuración rápida (stack trace centralizado)
- 📊 Transacciones de BD simples sin patrones Saga
- 👥 Coordinación directa para equipos pequeños
- 📈 Escalable a microservicios sin reescritura de lógica

---

## 📦 Instalación
## 📦 Instalación {#instalacion}

### Requisitos Previos
- Python 3.11+
- PostgreSQL 12+ (o SQLite para desarrollo)
- Git
- pip o conda

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Rojas-09/Proyecto_Hotel.git
   cd Proyecto_Hotel
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

5. **Inicializar base de datos**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. **Ejecutar la aplicación**
   ```bash
   flask run
   ```

   La aplicación estará disponible en `http://localhost:5000`

---

## 🚀 Uso
## 🚀 Uso {#uso}

### Inicio de Sesión
```
URL: http://localhost:5000/login
- Administrador: admin@hotel.com
- Recepcionista: recepcionista@hotel.com
- Gerente: gerente@hotel.com
```

### Casos de Uso Principales

#### 1. Realizar una Reserva (Cliente)
```
1. Consultar disponibilidad (rango de fechas)
2. Seleccionar habitación
3. Confirmar datos
4. Realizar pago (50% garantía)
5. Recibir confirmación por email
```

#### 2. Check-in/Check-out (Recepcionista)
```
Check-in:
- Verificar reserva
- Registrar entrada
- Generar comprobante

Check-out:
- Registrar salida
- Calcular total
- Procesar pago
```

#### 3. Ver Reportes (Gerente)
```
1. Acceder a Reportes
2. Seleccionar período
3. Descargar en Excel o PDF
```

---

## 👥 Roles y Permisos
## 👥 Roles y Permisos {#roles-y-permisos}

| Rol | Nivel de Acceso | Funciones |
|-----|--------------|-----------|
| **Administrador** | Total (Root) | Configuración global, gestión de usuarios, auditoría, parámetros |
| **Recepcionista** | Transaccional | Reservas, check-in/out, cargos adicionales |
| **Cliente/Huésped** | Limitado | Consulta de disponibilidad, reservas, ver puntos fidelidad |
| **Gerente** | Lectura | Reportes de ocupación, ingresos, análisis |

---

## 📁 Estructura del Proyecto
## 📁 Estructura del Proyecto {#estructura-del-proyecto}

```
Proyecto_Hotel/
├── app/
│   ├── __init__.py
│   ├── models/                    # Entidades de datos
│   │   ├── usuario.py
│   │   ├── reserva.py
│   │   ├── habitacion.py
│   │   ├── factura.py
│   │   └── ...
│   ├── services/                  # Lógica de negocio
│   │   ├── reserva_service.py
│   │   ├── factura_service.py
│   │   ├── pago_service.py
│   │   └── ...
│   ├── controllers/               # Endpoints API
│   │   ├── reserva_controller.py
│   │   ├── usuario_controller.py
│   │   └── ...
│   ├── templates/                 # HTML (Presentación)
│   │   ├── index.html
│   │   ├── login.html
│   │   └── ...
│   └── static/                    # CSS, JavaScript
│       ├── css/
│       └── js/
├── tests/                         # Suite de pruebas (pytest)
│   ├── test_reserva.py
│   ├── test_factura.py
│   └── ...
├── config.py                      # Configuración de la APP
├── requirements.txt               # Dependencias
├── .env.example                   # Variables de entorno
├── .gitignore
└── README.md
```

---

## 🔌 API REST
## 🔌 API REST {#api-rest}

### Autenticación
Todos los endpoints requieren **JWT (JSON Web Tokens)** en el header:
```
Authorization: Bearer <token>
```

### Endpoints Principales

#### Reservas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/reservas/disponibilidad` | Consultar disponibilidad |
| POST | `/api/reservas` | Crear reserva |
| PUT | `/api/reservas/{id}` | Modificar reserva |
| DELETE | `/api/reservas/{id}` | Cancelar reserva |
| GET | `/api/reservas` | Listar reservas |

#### Check-in/Check-out
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/checkin` | Registrar check-in |
| POST | `/api/checkout` | Registrar check-out |

#### Facturación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/facturas` | Generar factura |
| GET | `/api/facturas/{id}` | Obtener factura (PDF) |

#### Reportes
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/reportes/ocupacion` | Reporte de ocupación |
| GET | `/api/reportes/ingresos` | Reporte de ingresos |

### Documentación Completa de API
```
Swagger UI: http://localhost:5000/api/docs
```

---

## 📊 Requerimientos de Calidad

### Requerimientos Funcionales (RF)
- RF-01: Consulta disponibilidad < 500ms
- RF-02: Gestión completa de reservas
- RF-03: Notificaciones automáticas por email
- RF-04: Restricción de cambios < 24h
- RF-05: Control sincrónico de estados
- RF-06: Facturación automatizada (PDF)
- RF-07: CRUD de tipos de habitación
- RF-08: Exportación de reportes (Excel/PDF)
- RF-09: Seguridad por roles (JWT)
- RF-10: Gestión de comedor
- RF-11: Gestión de spa
- RF-12: Sistema de fidelización (10 puntos/noche)
- RF-13: Pasarela de pagos

### Requerimientos No Funcionales (RNF)
- ⚡ **Rendimiento**: 50 solicitudes concurrentes, latencia < 2s
- 🔒 **Seguridad**: bcrypt con factor 12 mínimo
- 📈 **Disponibilidad**: 99.5% uptime en producción
- 🎓 **Usabilidad**: Check-in en < 2 minutos
- 🔧 **Mantenibilidad**: Calificación "A" en PEP8 (flake8)

---

## 🔄 Flujo de Trabajo (Git)

### Ramas Principales
```
main          → Código productivo (tagged releases)
develop       → Integración de features
feature/*     → Nuevas funcionalidades
hotfix/*      → Correcciones urgentes
```

### Convención de Commits
```
feat:     Nueva funcionalidad
fix:      Corrección de errores
docs:     Cambios en documentación
refactor: Mejora de código
test:     Adición de pruebas
chore:    Tareas de mantenimiento
```

### Ejemplo
```bash
git commit -m "feat: integrar pasarela de pagos Stripe"
git commit -m "fix: validar fechas de salida en reserva"
```

---

## ✅ Testing y CI/CD
## ✅ Testing y CI/CD {#testing-y-cicd}

### Ejecutar Pruebas Locales
```bash
# Instalar dependencias de test
pip install pytest pytest-cov

# Ejecutar suite completa
pytest

# Con cobertura
pytest --cov=app tests/
```

### Pipeline de CI (GitHub Actions)
Cada Pull Request activa automáticamente:

1. **Linting** (flake8): Validación PEP8
2. **Tests** (pytest): Suite completa
3. **Quality Gate**: Mínimo 90% cobertura

---

## 📅 Hitos de Implementación
## 📅 Hitos de Implementación {#hitos-de-implementacion}

| Semana | Hito | Descripción |
|--------|------|-------------|
| 1-2 | Expansión BD | Nuevas entidades para servicios y fidelidad |
| 3-4 | Pasarela de Pagos | Integración SDK y validación en Staging |
| 5 | QA Final | Pruebas de carga y cobertura al 90% |

---

## 🤝 Guía de Contribución
## 🤝 Guía de Contribución {#guia-de-contribucion}

1. Crear rama: `git checkout -b feature/mi-funcionalidad`
2. Realizar cambios y commits
3. Seguir convención de commits
4. Crear Pull Request a `develop`
5. Esperar aprobación y merge

---

## 📝 Licencia
## 📝 Licencia {#licencia}
MIT License - Ver `LICENSE` para más detalles

---

## 📞 Contacto
## 📞 Contacto {#contacto}

- **Repositorio**: [GitHub - Proyecto_Hotel](https://github.com/Rojas-09/Proyecto_Hotel)
- **Rama Actual**: Development
- **Equipo**: Desarrolladores UTP
- **Email**: contacto@hotelbook.dev

---

**Última actualización**: Marzo 2026 | **Versión**: 1.0.0