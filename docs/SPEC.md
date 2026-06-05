# 📡 SPEC.md - HotelBook Pro API

**Versión:** 1.0 | **Fecha:** Mayo 2026

---

## 1. Módulos y Dependencias

### 1.1 Módulos del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    HOTELBOOK PRO API                       │
├─────────────────────────────────────────────────────────────┤
│  MÓDULO BASE (Auth + Habitaciones)                        │
│  ├── Usuario/Roles (autenticación, JWT, permisos)         │
│  ├── Habitación (tipos, precios, estado)                 │
│  └── Disponibilidad (verificación de fechas)              │
├─────────────────────────────────────────────────────────────┤
│  MÓDULO RESERVAS                                           │
│  ├── Reserva (crear, modificar, cancelar)                  │
│  ├── Check-in/Check-out                                    │
│  └── Historial                                             │
├─────────────────────────────────────────────────────────────┤
│  MÓDULO FACTURACIÓN                                        │
│  ├── Factura (generación con IVA 19%)                      │
│  ├── Pago (registro, reembolso)                           │
│  └── Pasarela de pagos (Stripe)                           │
├─────────────────────────────────────────────────────────────┤
│  MÓDULO SERVICIOS                                          │
│  ├── Comedor (pedidos vinculados a reserva)               │
│  ├── Spa (citas, validación de horarios)                  │
│  └── Fidelización (10 puntos/noche)                       │
├─────────────────────────────────────────────────────────────┤
│  MÓDULO REPORTES                                           │
│  ├── Ocupación                                             │
│  ├── Ingresos                                              │
│  └── Exportación (Excel/PDF)                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Orden de Implementación (Prioridad)

| # | Módulo | Descripción | Depende de |
|---|--------|-------------|------------|
| 1 | **Auth + Roles** | Login, JWT, bcrypt, permisos | Ninguno |
| 2 | **Habitaciones** | CRUD tipos, precios, disponibilidad | Ninguno |
| 3 | **Reservas** | Crear, modificar, cancelar, check-in/out | Auth, Habitaciones |
| 4 | **Facturación** | Facturas PDF, pagos, Stripe | Reservas |
| 5 | **Servicios** | Comedor, Spa, Fidelización | Reservas |
| 6 | **Reportes** | Estadísticas, exportación | Todo lo anterior |

---

## 2. Autenticación y Autorización

### 2.1 Roles de Usuario

| Rol | Permisos |
|-----|----------|
| `admin` | Total: gestión usuarios, configuración, auditoría |
| `recepcionista` | Reservas, check-in/out, cargos adicionales |
| `gerente` | Reportes, estadísticas (solo lectura) |
| `cliente` | Ver disponibilidad, propias reservas, puntos |

### 2.2 Autenticación JWT

```
Header: Authorization: Bearer <token>
Expira: 24 horas
Payload: { "user_id": int, "email": str, "role": str }
```

### 2.3 Endpoints de Auth

| Método | Endpoint | Descripción | Público |
|--------|----------|-------------|---------|
| POST | `/api/v1/auth/login` | Login usuario | ✅ |
| POST | `/api/v1/auth/register` | Registrar cliente | ✅ |
| POST | `/api/v1/auth/refresh` | Refresh token | ❌ |
| GET | `/api/v1/auth/me` | Datos usuario actual | ❌ |

---

## 3. Endpoints por Módulo

### 3.1 Módulo: Habitaciones

| Método | Endpoint | Descripción | Rol |
|--------|----------|-------------|-----|
| GET | `/api/v1/habitaciones` | Listar todas | Todos |
| GET | `/api/v1/habitaciones/{id}` | Detalle habitación | Todos |
| POST | `/api/v1/habitaciones` | Crear tipo habitación | Admin |
| PUT | `/api/v1/habitaciones/{id}` | Actualizar | Admin |
| DELETE | `/api/v1/habitaciones/{id}` | Eliminar tipo | Admin |
| GET | `/api/v1/habitaciones/disponibilidad` | Consultar disponibilidad | Todos |

**Parámetros disponibilidad:**

```
?fecha_entrada=2026-05-15&fecha_salida=2026-05-18
```

### 3.2 Módulo: Reservas

| Método | Endpoint | Descripción | Rol |
|--------|----------|-------------|-----|
| GET | `/api/v1/reservas` | Listar reservas | Admin/Recepcionista |
| GET | `/api/v1/reservas/mis-reservas` | Mis reservas | Cliente |
| GET | `/api/v1/reservas/{id}` | Detalle reserva | Propietario/Admin |
| POST | `/api/v1/reservas` | Crear reserva | Cliente |
| PUT | `/api/v1/reservas/{id}` | Modificar reserva | Propietario/Admin |
| DELETE | `/api/v1/reservas/{id}` | Cancelar reserva | Propietario/Admin |
| POST | `/api/v1/reservas/{id}/checkin` | Registrar check-in | Recepcionista |
| POST | `/api/v1/reservas/{id}/checkout` | Registrar check-out | Recepcionista |

**Validaciones:**

- fecha_salida > fecha_entrada
- Mínimo 24h de anticipación
- No overlaping con otra reserva

### 3.3 Módulo: Facturación

| Método | Endpoint | Descripción | Rol |
|--------|----------|-------------|-----|
| GET | `/api/v1/facturas` | Listar facturas | Admin/Recepcionista |
| GET | `/api/v1/facturas/{id}` | Ver factura (PDF) | Propietario/Admin |
| POST | `/api/v1/facturas` | Generar factura | Sistema (auto) |
| GET | `/api/v1/pagos` | Listar pagos | Admin/Recepcionista |
| POST | `/api/v1/pagos` | Registrar pago | Cliente |
| POST | `/api/v1/pagos/{id}/reembolso` | Solicitar reembolso | Admin |

**Factura:**

- IVA: 19% fijo
- Incluye: noches, servicios adicionales, garantía

### 3.4 Módulo: Servicios

#### Comedor (Pedidos)

| Método | Endpoint | Descripción | Rol |
|--------|----------|-------------|-----|
| GET | `/api/v1/comedor/pedidos` | Listar pedidos | Admin/Recepcionista |
| POST | `/api/v1/comedor/pedidos` | Crear pedido | Cliente (hospedado) |
| GET | `/api/v1/comedor/menu` | Ver menú | Todos |

#### Spa

| Método | Endpoint | Descripción | Rol |
|--------|----------|-------------|-----|
| GET | `/api/v1/spa/citas` | Listar citas | Admin/Cliente |
| POST | `/api/v1/spa/citas` | Agendar cita | Cliente (hospedado) |
| PUT | `/api/v1/spa/citas/{id}` | Modificar cita | Cliente/Admin |
| DELETE | `/api/v1/spa/citas/{id}` | Cancelar cita | Cliente/Admin |

**Validación Spa:** No permitir citas que se traslapen en horario.

#### Fidelización

| Método | Endpoint | Descripción | Rol |
|--------|----------|-------------|-----|
| GET | `/api/v1/fidelizacion/puntos` | Ver puntos | Cliente |
| GET | `/api/v1/fidelizacion/canjes` | Canjes disponibles | Cliente |
| POST | `/api/v1/fidelizacion/canjear` | Canjear puntos | Cliente |

**Regla:** 10 puntos por noche efectiva.

### 3.5 Módulo: Reportes

| Método | Endpoint | Descripción | Rol |
|--------|----------|-------------|-----|
| GET | `/api/v1/reportes/ocupacion` | % ocupación | Gerente/Admin |
| GET | `/api/v1/reportes/ingresos` | Ingresos período | Gerente/Admin |
| GET | `/api/v1/reportes/ocupacion/excel` | Exportar Excel | Gerente/Admin |
| GET | `/api/v1/reportes/ocupacion/pdf` | Exportar PDF | Gerente/Admin |

**Parámetros:**

```
?fecha_inicio=2026-01-01&fecha_fin=2026-12-31
```

---

## 4. Formato de Respuestas

### 4.1 Respuesta Exitosa

```json
{
  "success": true,
  "data": { ... },
  "message": "Operación exitosa",
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

### 4.2 Respuesta de Error

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "La fecha de salida debe ser posterior a la fecha de entrada",
    "details": [
      { "field": "fecha_salida", "error": "debe ser mayor a fecha_entrada" }
    ]
  }
}
```

### 4.3 Códigos de Error

| Código | HTTP Status | Descripción |
|--------|-------------|-------------|
| `UNAUTHORIZED` | 401 | No autenticado |
| `FORBIDDEN` | 403 | Sin permisos |
| `NOT_FOUND` | 404 | Recurso no existe |
| `VALIDATION_ERROR` | 400 | Error de validación |
| `CONFLICT` | 409 | Conflicto (overbooking) |
| `INTERNAL_ERROR` | 500 | Error del servidor |

---

## 5. Esquemas de Datos (Básico)

### Usuario

```python
{
  "id": int,
  "email": str,
  "nombre": str,
  "apellido": str,
  "telefono": str,
  "rol": "admin|recepcionista|gerente|cliente",
  "puntos_fidelizacion": int,
  "created_at": datetime
}
```

### Habitación

```python
{
  "id": int,
  "tipo": "estandar|premium|suite",
  "numero": str,
  "planta": int,
  "precio_noche": decimal,
  "capacidad": int,
  "estado": "disponible|ocupada|mantenimiento",
  "descripcion": str,
  "imagenes": [str]
}
```

### Reserva

```python
{
  "id": int,
  "usuario_id": int,
  "habitacion_id": int,
  "fecha_entrada": date,
  "fecha_salida": date,
  "estado": "confirmada|checkin|checkout|cancelada",
  "total": decimal,
  "garantia_pagada": bool,
  "created_at": datetime
}
```

### Factura

```python
{
  "id": int,
  "reserva_id": int,
  "cliente_id": int,
  "subtotal": decimal,
  "iva": decimal,  # 19%
  "total": decimal,
  "items": [
    { "descripcion": str, "cantidad": int, "precio": decimal }
  ],
  "fecha_emision": datetime,
  "estado": "pagada|pendiente|reembolsada"
}
```

---

## 6. Validaciones de Negocio

| Regla | Descripción |
|-------|-------------|
| R1 | Reserva mínima 1 noche |
| R2 | Modificación no permitida < 24h antes |
| R3 | Cancelación con reembolso según política |
| R4 | Garantía 50% para confirmar reserva |
| R5 | Check-in: hora mínima 14:00 |
| R6 | Check-out: hora máxima 12:00 |
| R7 | Spa: no permitir citas superpuestas |
| R8 | Fidelización: 10 puntos/noche efectiva |
| R9 | Auth: Un usuario no puede eliminarse ni desactivarse a sí mismo |

---

## 7. Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | Mayo 2026 | Primera versión API |
| 1.0.1 | Mayo 2026 | Módulo Auth implementado (registro, login, JWT) |
| 1.0.2 | Mayo 2026 | Regla de negocio Auth: prevenir auto-eliminación y auto-desactivación |

---

## 8. Notas de Implementación

1. **Módulo base (Auth + Habitaciones)** debe implementarse primero
2. Todos los endpoints de escritura requieren JWT válido
3. Los roles se verifican en cada endpoint
4. Pagination en endpoints de lista (20 ítems por página)
5. Logs de todas las operaciones (auditoría)
