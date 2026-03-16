# ✅ CHECKLIST DE CUMPLIMIENTO - Requisitos de Evaluación

**HotelBook Pro - Verificación de Requisitos**  
Última actualización: Marzo 2026

---

## 📌 PARTE 1: REPOSITORIO GIT EN GITHUB

### Requisito: Crear repositorio con README, estructura y commits documentados

#### ✅ Verificar que el repositorio existe en GitHub:

```bash
# 1. Confirmar que estás conectado a GitHub
git remote -v
```

**Esperado:**
```
origin  https://github.com/Rojas-09/Proyecto_Hotel.git (fetch)
origin  https://github.com/Rojas-09/Proyecto_Hotel.git (push)
```

**Acción:** Si falta, ejecutar:
```bash
git remote add origin https://github.com/Rojas-09/Proyecto_Hotel.git
```

---

#### ✅ 1.1 README.md Presente y Profesional

**Comando para verificar:**
```bash
ls -la README.md
```

**Debe existir:** ✅ 

**Checklist del README:**
- [ ] Título y descripción clara
- [ ] Tabla de contenidos
- [ ] Instrucciones de instalación
- [ ] Stack tecnológico documentado
- [ ] Estructura del proyecto
- [ ] Ejemplos de uso
- [ ] Guía de contribución
- [ ] Contacto/Info del equipo
- [ ] Licencia

**Verificar calidad:**
```bash
# Abrir en VS Code
code README.md
```

**Se debe ver:** Profesional, bien formateado con Markdown, fácil de leer.

---

#### ✅ 1.2 Estructura del Proyecto Organizada

**Comando para verificar:**
```bash
tree -L 2 -I '__pycache__|*.pyc|.git|venv'
```

**Estructura esperada (mínimo):**
```
Proyecto_Hotel/
├── README.md                    ✅
├── FLUJO_DESARROLLO.md          ✅ (Este documento)
├── requirements.txt             ✅
├── .gitignore                   ✅
├── .env.example                 ✅
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── services/
│   ├── controllers/
│   ├── templates/
│   └── static/
├── tests/
│   ├── __init__.py
│   ├── test_reserva.py
│   └── test_factura.py
└── config.py                    ✅
```

**Checklist de estructura:**
- [ ] Carpeta `app/` con módulos organizados
- [ ] Carpeta `tests/` con pruebas
- [ ] Archivo `requirements.txt` con dependencias
- [ ] `.gitignore` configurado
- [ ] `.env.example` como plantilla
- [ ] `config.py` o configuración centralizada

---

#### ✅ 1.3 Commits Documentados (IMPORTANTE)

**Comando para ver commits:**
```bash
git log --oneline -20
```

**Esperado:**
```
a1b2c3d feat: integrar pasarela de pagos Stripe
e4f5g6h fix: validar fechas en reserva
i7j8k9l docs: actualizar README con endpoints
m0n1o2p refactor: optimizar cálculo de impuestos
q3r4s5t test: aumentar cobertura de factura.py
u6v7w8x chore: actualizar dependencias
```

**Checklist de calidad de commits:**
- [ ] Commits usan convención: `tipo(scope): descripción`
- [ ] Los 10 últimos commits tienen mensajes descriptivos
- [ ] Ningún commit dice `wip`, `fix`, `update` sin contexto
- [ ] Commits son atómicos (una funcionalidad por commit)
- [ ] Mensajes son en inglés o español consistente

**Puntos por commit:**
```
✅ Excelente: feat: integrar validación de fechas en reserva
✅ Bueno:    fix: corregir cálculo doble de IVA en reembolso
⚠️  Aceptable: update dependencies
❌ Malo:      wip, fix, updated, stuff
```

**¿Cómo mejorar los commits ahora?**

Si tienes commits malos en `develop`, puedes reescribir el historial:
```bash
# WARNING: Solo hacer si no está en shared branches
git rebase -i HEAD~5  # Últimos 5 commits
```

Pero **mejor opción:** Hacer commits buenos a partir de ahora.

---

### Resumen Parte 1:

| Requisito | Verificación | Estado |
|-----------|-------------|--------|
| Repositorio en GitHub | `git remote -v` | ✅ |
| README profesional | Existe + bien formateado | ✅ |
| Estructura organizada | Carpetas lógicas | ✅ |
| Commits documentados | `git log` con buen formato | ✅ |

---

## 📌 PARTE 2: ESTRATEGIA DE RAMAS (Branching)

### Requisito: Definir main, develop, feature + explicar flujo

#### ✅ 2.1 Verificar que existen las ramas

**Comando:**
```bash
git branch -a
```

**Debe mostrar:**
```
* develop
  main
  remotes/origin/develop
  remotes/origin/main
```

**Si faltan ramas, crearlas:**

```bash
# Crear main (si no existe)
git checkout -b main

# Crear develop (si no existe)
git checkout -b develop

# Subir al repo
git push -u origin main
git push -u origin develop
```

---

#### ✅ 2.2 Configurar rama por defecto

**En GitHub:**
1. Ir a Repo → Settings
2. Default branch: Select **develop**
3. Click Update

**Verificar en terminal:**
```bash
git config --get init.defaultBranch
# Debe mostrar: develop
```

---

#### ✅ 2.3 Definir el flujo de ramas (Documentación)

**Verificar que existe explicación:**

El archivo `FLUJO_DESARROLLO.md` (que ya creamos) debe contener:

- [ ] Explicación de qué es cada rama
- [ ] Cuándo crearlas
- [ ] Cómo usarlas
- [ ] Diagramas visuales
- [ ] Ejemplo de workflow con `main`, `develop`, `feature/*`

**Contenido esperado en FLUJO_DESARROLLO.md:**
```markdown
## Ramas Principales

- **main**: Código productivo (estable, taggeado)
- **develop**: Integración de features
- **feature/***:Nuevas funcionalidades

## Flujo
1. Crear feature de develop
2. Trabajar en feature
3. PR a develop
4. Merge a develop después de aprobar
5. Cuando listo, hacer release: merge develop → main
```

---

### Resumen Parte 2:

| Requisito | Verificación | Comando |
|-----------|-------------|---------|
| Rama main existe | `git branch -a` | ✅ |
| Rama develop existe | `git branch -a` | ✅ |
| Rama feature creándose | Crear cuando sea necesario | ✅ |
| Flujo documentado | FLUJO_DESARROLLO.md | ✅ |

---

## 📌 PARTE 3: DOCUMENTO DE FLUJO DE DESARROLLO

### Requisito: Explicar cómo desarrolla, commitea y mergea

#### ✅ 3.1 Debe existir documento oficial

**Verificar:**
```bash
ls -la FLUJO_DESARROLLO.md
```

**Debe existir:** ✅ (Ya lo creamos)

---

#### ✅ 3.2 El documento debe explicar:

**Sección 1: Iniciar una funcionalidad**
```markdown
## Paso 1: Crear feature
- [ ] git checkout develop
- [ ] git pull origin develop
- [ ] git checkout -b feature/nombre-descriptivo

## Paso 2: Desarrollar
- [ ] Editar archivos
- [ ] Probar cambios
- [ ] Ejecutar tests
```

---

**Sección 2: Hacer commits**
```markdown
## Convención de Commits

feat: Nueva funcionalidad
fix: Corrección de bug
docs: Documentación
refactor: Mejora de código
test: Pruebas
chore: Mantenimiento

## Ejemplos BUENOS:
git commit -m "feat(reservas): agregar validación de fechas"

## Ejemplos MALOS:
git commit -m "fix"
git commit -m "updated"
```

---

**Sección 3: Hacer merge**
```markdown
## Crear Pull Request

1. git push origin feature/nombre
2. Ir a GitHub
3. Click "New Pull Request"
4. Base: develop
5. Compare: feature/nombre
6. Describir cambios
7. Enviar

## Merge después de aprobación

- En GitHub: Click "Merge Pull Request"
- Or localmente: git merge feature/nombre
```

---

#### ✅ 3.3 Verificar contenido del documento

**Checklist:**
- [ ] Explicacion clara de main y develop
- [ ] Paso a paso para crear feature
- [ ] Paso a paso para hacer commits
- [ ] Paso a paso para pull requests
- [ ] Paso a paso para merge
- [ ] Ejemplos de commits buenos vs malos
- [ ] Resolución de conflictos
- [ ] Troubleshooting común
- [ ] Comandos útiles
- [ ] Buenas prácticas del equipo

**Ver el documento:**
```bash
cat FLUJO_DESARROLLO.md | head -50
```

---

## 🎯 RESUMEN FINAL: LISTA MAESTRA DE VERIFICACIÓN

### ✅ Requisito 1: REPOSITORIO GIT

```bash
# Ejecutar en terminal:
echo "=== Verificando Repositorio ==="
git remote -v                           # Debe mostrar GitHub
ls -la README.md                        # Debe existir
git log --oneline -5                    # Ver commits
tree -L 2                               # Ver estructura
```

**Checklist:**
- [ ] Repository en GitHub (Rojas-09/Proyecto_Hotel)
- [ ] README.md existe y está profesional
- [ ] Estructura de carpetas organizada (app/, tests/, config/)
- [ ] Al menos 10 commits con mensajes documentados
- [ ] Commits siguen patrón: `feat/fix/docs/refactor/test/chore`
- [ ] `.gitignore` configurado (incluye `__pycache__`, `*.pyc`, `venv/`, `.env`)

**Evaluación será:**
- Mensajes de commit: ⭐⭐ (formato + descriptivos)
- Historial: ⭐⭐ (lógica + atomicidad)
- Organización: ⭐⭐ (carpetas + README)

---

### ✅ Requisito 2: ESTRATEGIA DE RAMAS

```bash
# Ejecutar en terminal:
echo "=== Verificando Ramas ==="
git branch -a                           # Ver todas las ramas
git log main --oneline -3               # Ver commits en main
git log develop --oneline -3            # Ver commits en develop
```

**Checklist:**
- [ ] Rama `main` existe y tiene código stable (puede estar vacía)
- [ ] Rama `develop` existe y tiene código integrado
- [ ] Rama `feature/ejemplo` ha sido creada en algún momento
- [ ] `.gitignore` previene commits accidentales
- [ ] Se entiende claramente cuándo usar cada rama

**Documentación esperada en README.md o FLUJO_DESARROLLO.md:**

```markdown
## Ramas del Proyecto

### main (Rama de Producción)
- Código estable y probado
- Solo se reciben PRs de develop y hotfix
- Todos los commits están taggeados con versión

### develop (Rama de Integración)
- Rama base para nuevos features
- Contiene código de pre-release
- Base para crear feature branches

### feature/* (Ramas de Características)
- Se crean desde develop
- Nombre descriptivo: feature/validar-fechas
- Se deletan después del merge
```

---

### ✅ Requisito 3: DOCUMENTO DE FLUJO

```bash
# Verificar que existe:
cat FLUJO_DESARROLLO.md
```

**Checklist:**
- [ ] Archivo `FLUJO_DESARROLLO.md` existe en raíz del proyecto
- [ ] Explica cómo CREAR una funcionalidad (create feature, develop)
- [ ] Explica cómo HACER COMMIT (convención de mensajes)
- [ ] Explica cómo HACER MERGE (pull request, merge a develop)
- [ ] Incluye ejemplos prácticos
- [ ] Incluye comandos Git recomendados
- [ ] Instrucciones para resolver conflictos
- [ ] Guía de troubleshooting

**Secciones mínimas requeridas:**

1. **Iniciando una funcionalidad**
   ```
   Paso 1: Cambiar a develop y traer cambios
   git checkout develop && git pull origin develop
   
   Paso 2: Crear feature
   git checkout -b feature/nombre
   ```

2. **Haciendo commits**
   ```
   Formato: tipo(scope): descripción
   Ejemplo: feat(reservas): agregar validación de fechas
   ```

3. **Haciendo merge (Pull Request)**
   ```
   1. Push a GitHub
   2. Crear PR a develop
   3. Esperar aprobación
   4. Merge desde GitHub
   ```

---

## 🎓 CÓMO USAR ESTA CHECKLIST

### Para validar que cumples:

```bash
# 1. Clonar el repo completo
git clone https://github.com/Rojas-09/Proyecto_Hotel.git

# 2. Ejecutar verificaciones
git remote -v                    # ✅ Verificar repo
ls -la README.md               # ✅ Ver README
git log --oneline -20          # ✅ Ver commits
git branch -a                  # ✅ Ver ramas
cat FLUJO_DESARROLLO.md        # ✅ Ver flujo

# 3. Tickear cada item de abajo
```

---

## ✨ RESULTADO ESPERADO

Si todo está correcto, un evaluador verá:

### En GitHub
```
✅ README.md profesional y completo
✅ Estructura de carpetas bien organizada
✅ main y develop branches visibles
✅ Commits con mensajes claros en el historial
✅ PRs con documentación
✅ Tags/versiones marcadas
```

### En Terminal
```bash
$ git log --oneline -10
a1b2c3d feat: integrar pasarela de pagos
e4f5g6h feat: agregar validación de fechas
i7j8k9l fix: corregir cálculo de IVA
m0n1o2p docs: actualizar README
q3r4s5t test: aumentar cobertura

$ git branch -a
  develop
  main
* remotes/origin/develop
  remotes/origin/main
```

### En Estructura
```
✅ README.md (profesional)
✅ FLUJO_DESARROLLO.md (completo)
✅ requirements.txt (lista de dependencias)
✅ .gitignore (configurado)
✅ app/ (code modular)
✅ tests/ (pruebas)
```

---

## 📞 DUDAS FRECUENTES

### P: ¿Mis commits están bien si tengo que hacerlos ahora?
**R:** Sí. Haz commits con buenos mensajes desde ahora en adelante. Los commits anteriores no se pueden cambiar sin reescribir historia.

### P: ¿Debo tener 50 commits?
**R:** No. Calidad > cantidad. 10-15 commits bien documentados es mejor que 50 malos.

### P: ¿La rama main debe tener código?
**R:** Idealmente sí, pero en desarrollo se puede tener vacía. `develop` definitivamente debe tener código.

### P: ¿Puedo mergear sin PR?
**R:** Técnicamente sí, pero **no deberías**. Los PRs son para documentar cambios.

### P: ¿Qué pasa si tengo conflictos?
**R:** Léel sección "Resolución de conflictos" en FLUJO_DESARROLLO.md

---

**¡Listo para evaluación! Usa esta checklist para validar todo. ✅**
