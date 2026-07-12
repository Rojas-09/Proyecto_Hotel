# Deploy — HotelBook Pro

## Stack objetivo

```
Frontend (Vue 3 + Nginx)  →  Backend (Flask + Gunicorn)  →  PostgreSQL
         :80                        :5000                        :5432
```

## Opciones gratuitas con GitHub Student

### Opción A: Render (recomendada — más simple)

| Servicio | Precio | Detalle |
|----------|--------|---------|
| Web Service | Gratis | 512 MB RAM, 1 CPU — backend + frontend |
| PostgreSQL | Gratis | 1 GB storage |

**Pasos:**
1. Ir a [render.com](https://render.com) → "Sign up with GitHub"
2. Dashboard → **New Web Service** → conectar repo
3. Configurar:
   - **Root Directory:** `.`
   - **Runtime:** Docker
   - **Plan:** Free
4. Agregar Environment Variables:
   - `SECRET_KEY`: `<generar con: python3 -c "import secrets; print(secrets.token_hex(32))">`
   - `CORS_ORIGINS`: `https://<tu-dominio>.onrender.com`
5. Crear **New PostgreSQL** (plan Free)
6. En Web Service → Environment → agregar:
   - `DATABASE_URL`: copiar de PostgreSQL dashboard
7. Deploy automático desde GitHub

### Opción B: Railway (más control)

| Servicio | Precio |
|----------|--------|
| 2 servicios + DB | $0 con GH Student |

**Pasos:**
1. [railway.app](https://railway.app) → GitHub login
2. **New Project** → Deploy from GitHub repo
3. Add **PostgreSQL** plugin
4. Railway detecta `docker-compose.yml` automáticamente
5. Agregar `SECRET_KEY` y `CORS_ORIGINS` en variables de entorno

### Opción C: Fly.io (más técnico)

| Servicio | Precio |
|----------|--------|
| 3 apps siempre activas | Gratis |
| PostgreSQL | $0 (dev plan) |

**Pasos:**
1. `flyctl launch` desde el repo
2. Sigue el wizard — Fly detecta el Dockerfile
3. `flyctl postgres create` para la DB
4. `flyctl secrets set SECRET_KEY=...`

---

## Dominio propio

### 1. Comprar dominio
- **Namecheap** / **Porkbun** / **Cloudflare Registrar**
- Precio ≈ $8–12/año
- Si ya tienes uno, saltas este paso

### 2. DNS (Cloudflare — gratis)
1. Crear cuenta en [Cloudflare](https://cloudflare.com)
2. Agregar tu dominio
3. Cloudflare te da **nameservers** → cambiarlos en tu registrar
4. DNS → **Add Record**:
   ```
   Tipo: CNAME
   Nombre: @
   Destino: <tu-app>.onrender.com  (o railway.app, o fly.dev)
   Proxy: ✅
   ```

### 3. SSL
- **Render/Railway/Fly** incluyen SSL automático con Let's Encrypt
- **Cloudflare** también da SSL flexible/Full

### 4. Configurar CORS
En Render/Railway/Fly → Environment Variables:
```
CORS_ORIGINS=https://tudominio.com,https://www.tudominio.com
```

---

## Notas importantes

### Secret Key
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# → pegar en SECRET_KEY del servicio
```

### Static files (facturas PDF, reportes)
Render y Railway usan **ephemeral storage** — los PDF se pierden al redeploy.
Soluciones:
- **Local:** los PDF se guardan en el volumen `static_data` (Docker)
- **Producción:** migrar a S3-compatible (Backblaze B2, $0.006/GB/mes)

### Comandos útiles

```bash
# Local con Docker
docker compose up -d --build
docker compose logs -f backend

# Ver tests
docker compose exec backend pytest tests/ -q
```
