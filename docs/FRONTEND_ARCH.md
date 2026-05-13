# Arquitectura Frontend - HotelBook Pro

Esta guía describe la estructura modular y escalable implementada para la capa de presentación del sistema. Se ha diseñado siguiendo principios de separación de responsabilidades y organización por roles.

## 📁 Estructura de Carpetas

### 1. Templates (`app/templates/`)
Organizados por contexto de usuario y layouts compartidos:
- `layouts/`: Plantillas base (Jinja2) que contienen la estructura HTML común (Navbar, Footer, Scripts globales).
- `public/`: Vistas para usuarios no autenticados (Home, Detalle Habitación, Login).
- `cliente/`: Vistas privadas para huéspedes (Mis Reservas, Perfil, Pagos).
- `recepcionista/`: Panel operativo (Check-in/out, Gestión de servicios).
- `admin/`: Panel administrativo (Reportes, Gestión de usuarios/habitaciones).

### 2. Static Assets (`app/static/`)
Separación estricta de CSS y JS por rol para evitar colisiones de estilos y scripts pesados:
- `css/`:
  - `global.css`: Variables de marca, tipografía premium y componentes comunes (botones, inputs).
  - `public/`, `cliente/`, `recepcionista/`, `admin/`: Estilos específicos para cada módulo.
- `js/`:
  - `global.js`: Utilidades comunes (formateo de moneda, validaciones base).
  - `public/`, `cliente/`, `recepcionista/`, `admin/`: Lógica específica de cada vista.

## 🎨 Estándares de Diseño (Premium)

- **Tipografía**: 
  - Títulos: `Playfair Display` (Serif elegante).
  - Cuerpo: `Inter` (Sans-serif moderna y legible).
- **Colores**:
  - Navy Profundo (`#0f172a`): Autoridad y elegancia.
  - Dorado Mate (`#b4944a`): Lujo y exclusividad.
- **Componentes**: Uso de sombras suaves (`box-shadow`), bordes redondeados (`16px` para tarjetas) y transiciones fluidas.

## 🚀 Cómo agregar una nueva vista

1. **HTML**: Crea el archivo en la carpeta del rol correspondiente (ej. `app/templates/cliente/mis_reservas.html`).
2. **Extender Layout**: Usa `{% extends "layouts/base_public.html" %}` (o el layout que corresponda).
3. **CSS/JS**: Crea los archivos en `app/static/css/[rol]/` y `app/static/js/[rol]/`.
4. **Inyectar Assets**: Usa los bloques `extra_css` y `extra_js` en tu template para cargar solo lo necesario.

```html
{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/cliente/reservas.css') }}">
{% endblock %}
```

## 🛠️ Mejores Prácticas
- **No Inline Styles**: Todo el CSS debe ir en archivos `.css`.
- **Modularidad**: Si un componente se repite en más de 2 roles, muévelo a `global.css`.
- **Responsive**: Diseñar siempre pensando en dispositivos móviles primero.
- **Accesibilidad**: Usar etiquetas semánticas (`<article>`, `<nav>`, `<main>`).
