# 📋 FLUJO DE DESARROLLO - HotelBook Pro

**Documento oficial del flujo de trabajo del equipo**  
Versión: 1.0 | Última actualización: Marzo 2026

---

## 1. Estrategia de Ramas (Git Flow Simplificado)

### 1.1 Estructura de Ramas

```
main (rama de producción - STABLE)
 ├── develop (rama de integración - PRE-RELEASE)
 │   ├── feature/reservas
 │   ├── feature/facturacion
 │   ├── feature/spa-comedor
 │   └── feature/fidelizacion
 │
 └── hotfix/bug-critico (extraída de main)
```

### 1.2 Descripción de Ramas

| Rama | Propósito | Creada desde | Mergeada a | Duración |
|------|----------|-------------|-----------|----------|
| **main** | Código productivo, estable y taggeado | N/A | N/A | Permanente |
| **develop** | Integración de features completados | main | main | Permanente |
| **feature/*** | Desarrollo de funcionalidades nuevas | develop | develop (PR) | Temporal (1-2 semanas) |
| **hotfix/*** | Correcciones críticas de production | main | main + develop | Temporal (1-3 días) |

### 1.3 Reglas de las Ramas

- ✅ **main** solo recibe merges desde `develop` y `hotfix`
- ✅ **develop** es la rama base para nuevos features
- ✅ **feature/** nunca se crean de main
- ✅ **Nadie commitea directamente** a main o develop (solo por PR)

---

## 2. Flujo de Trabajo: Paso a Paso

### 2.1 Iniciando una Nueva Funcionalidad

#### Paso 1: Actualizar develop localmente
```bash
# Asegurarse de estar en develop
git checkout develop

# Traer cambios del repositorio remoto
git pull origin develop

# Verificar que todo está limpio
git status
# Debe mostrar: On branch develop, nothing to commit, working tree clean
```

#### Paso 2: Crear rama de feature
```bash
# Crear y cambiar a nueva rama
git checkout -b feature/nombre-descriptivo

# Las ramas deben tener nombres claros:
# ✅ CORRECTO:
#   - feature/validar-fechas-reserva
#   - feature/integrar-stripe
#   - feature/reportes-ocupacion

# ❌ INCORRECTO:
#   - feature/fix1
#   - feature/nueva-cosa
#   - feature/wip
```

#### Paso 3: Desarrollar la funcionalidad

```bash
# Hacer cambios en los archivos
# Ejemplo: editar app/services/reserva_service.py

# Verificar cambios
git status

# Staging (preparar para commit)
git add app/services/reserva_service.py

# O agregar todo (cuidado)
git add .
```

---

### 2.2 Realizando Commits

#### Convención de Commits (MUY IMPORTANTE)

```
<tipo>(<scope>): <descripción corta>

<descripción detallada (opcional pero recomendada)>

<referencias o notas>
```

#### Tipos de Commits Permitidos

| Tipo | Significado | Ejemplo |
|------|-----------|---------|
| **feat** | Nueva funcionalidad | `feat(reservas): agregar validación de fechas` |
| **fix** | Corrección de bug | `fix(factura): corregir cálculo de IVA` |
| **docs** | Cambios en documentación | `docs: actualizar README con endpoints` |
| **refactor** | Mejora de código sin cambiar función | `refactor(pago): optimizar validaciones` |
| **test** | Agregar o modificar tests | `test(reserva): aumentar cobertura al 95%` |
| **chore** | Tareas de mantenimiento | `chore: actualizar dependencias en requirements.txt` |
| **style** | Cambios de formato (no lógica) | `style: formatear código con black` |

#### Ejemplos de Commits Buenos vs Malos

✅ **COMMITS BUENOS:**
```bash
git commit -m "feat(reservas): agregar validación de fechas

- Valida que fecha_salida > fecha_entrada
- Prohíbe reservas con menos de 24h
- Retorna error HTTP 400 con mensaje descriptivo"

git commit -m "fix(factura): corregir cálculo de IVA

El sistema aplicaba IVA dos veces en reembolsos.
Se corrigió la lógica en FacturaService.calcular_total()"

git commit -m "test(reserva): aumentar cobertura de test_create_reserva

Coverage pasó de 85% a 95% en módulo reservas"
```

❌ **COMMITS MALOS:**
```bash
git commit -m "fix stuff"              # Muy vago
git commit -m "wip"                    # Sin descripción
git commit -m "updated"                # No especifica qué
git commit -m "fix: fix fix fix"       # Repetitivo
git commit -m "feat: todo"             # Demasiado genérico
```

#### Hacer un Commit Correcto

```bash
# Opción 1: Mensaje simple (features pequeñas)
git commit -m "feat(comedor): crear endpoint POST para pedidos"

# Opción 2: Mensaje con descripción (features complejas)
git commit -m "feat(fidelizacion): implementar acumulación automática de puntos

- Se añade trigger en doCheckOut()
- Se calcula 10 puntos por noche efectiva
- Se actualiza tabla PuntosFidelidad
- Se notifica al cliente por email
- Coverage: 92%"

# Opción 3: Mensaje interactivo (recomendado)
git commit
# Se abrirá editor de texto (vim/nano)
# Escribir el mensaje con más detalle
```

---

### 2.3 Haciendo Push y Creando Pull Request

#### Paso 1: Push a origin
```bash
# Subir la rama al repositorio remoto
git push origin feature/nombre-descriptivo

# Primera vez en la rama, especificar upstream:
git push -u origin feature/nombre-descriptivo
```

#### Paso 2: Crear Pull Request en GitHub

1. **Ir a GitHub** → Repo → Pull Requests
2. **Clickear "New Pull Request"**
3. **Comparar ramas:**
   - Base: `develop`
   - Compare: `feature/tu-rama`

4. **Llenar el formulario:**

```markdown
## Descripción
Breve descripción de qué hace este PR

## Tipo de cambio
- [ ] feat: Nueva funcionalidad
- [ ] fix: Corrección de bug
- [ ] docs: Actualización de documentación
- [ ] refactor: Mejora de código
- [ ] test: Aumento de cobertura

## Testing
- [ ] Las pruebas pasan localmente
- [ ] Se agregaron tests nuevos
- [ ] Cobertura >= 90%

## Checklist
- [ ] Commits siguen la convención
- [ ] README actualizado
- [ ] Sin errores de linting (flake8)
- [ ] No hay conflictos con develop

## Screenshots (si aplica)
[Adjuntar capturas de UI]

## Referencias
Cierra #123 (si está vinculado a un issue)
```

5. **Clickear "Create Pull Request"**

---

### 2.4 Revisión de Código y Aprobación

#### Qué busca el revisor:

```
✅ Commits documentados adecuadamente
✅ Código limpio (flake8 sin errores)
✅ Tests con cobertura >= 90%
✅ Falta documentación o actualización del README
✅ Sin conflictos con develop
✅ La funcionalidad cumple los requerimientos
```

#### Como revisor, dar feedback:

```bash
# GitHub permite comentar línea por línea
# 1. Clickear en línea de código
# 2. Escribir comentario
# 3. Proponer cambios o preguntar

# El autor entonces hace cambios y:
git add .
git commit -m "review: aplicar feedback de revisión"
git push origin feature/nombre-descriptivo
```

---

### 2.5 Mergeando a Develop

#### Opción A: Merge vía GitHub (RECOMENDADO)
```
En el PR de GitHub:
1. Esperar aprobación del revisor ✅
2. Resolver conflictos si los hay
3. Clickear "Merge pull request"
4. Confirmar: "Confirm merge"
5. Opcionalmente: "Delete branch"
```

#### Opción B: Merge local (si es necesario)
```bash
# Cambiar a develop
git checkout develop

# Traer cambios remotos
git pull origin develop

# Mergear la rama de feature
git merge feature/nombre-descriptivo

# Subir los cambios
git push origin develop
```

#### Resolver Conflictos (si los hay)
```bash
# Si hay conflicto, Git lo marca:
git merge feature/nombre-descriptivo
# CONFLICT (content): Merge conflict in app/models/reserva.py

# Abrir el archivo y buscar:
# <<<<<<< HEAD
# código en develop
# =======
# código en feature
# >>>>>>> feature/nombre-descriptivo

# Editar manualmente para resolver

# Luego:
git add app/models/reserva.py
git commit -m "merge: resolver conflictos al mergear feature/xxx"
git push origin develop
```

---

### 2.6 Limpiar las Ramas Locales

```bash
# Después de mergear, borrar rama local
git branch -d feature/nombre-descriptivo

# Si hay cambios sin mergear (forzar):
git branch -D feature/nombre-descriptivo

# Ver ramas locales disponibles
git branch -a
```

---

## 3. Flujo de Hotfix (Correcciones Críticas)

### Cuando usar hotfix:
- Bug crítico en producción (main)
- Falla de seguridad
- Error que afecta usuarios

### Proceso:
```bash
# 1. Partir desde main
git checkout main
git pull origin main

# 2. Crear rama hotfix
git checkout -b hotfix/descripcion-critica

# 3. Hacer fix y commit
# ... editar archivos ...
git add .
git commit -m "fix(critico): describe el problema y solución"

# 4. Subir
git push -u origin hotfix/descripcion-critica

# 5. Crear PR a main (no a develop)
# En GitHub: PR Base: main, Compare: hotfix/...

# 6. Una vez aprobado y mergeado a main:
git checkout develop
git pull origin main
git merge main

# Para asegurar que la corrección esté también en develop
```

---

## 4. Pipeline de CI/CD (Validaciones Automáticas)

Cada push a una rama activa automáticamente en GitHub Actions:

### Para feature branches:
```yaml
✓ Linting (flake8): Validar sintaxis PEP8
✓ Tests (pytest): Ejecutar suite completa
✓ Coverage: Validar >= 90%
✗ Si falla algo: No permitir merge a develop
```

### Para develop:
```yaml
✓ Linting
✓ Tests  
✓ Coverage >= 90%
✓ Build Docker (si aplica)
✓ Deploy a Staging
```

### Para main:
```yaml
✓ Todo lo anterior
✓ Deploy a Producción
✓ Crear Release tag
✓ Generar Release Notes
```

**Ver estado del CI:**
```bash
# En GitHub Actions tab
# O en el PR: checkear "Checks" sección
```

---

## 5. Versionado Semántico (SemVer)

Las versiones siguen: `MAJOR.MINOR.PATCH`

| Incremento | Cuándo | Ejemplo |
|-----------|--------|---------|
| **MAJOR** | Cambios incompatibles | 1.0.0 → 2.0.0 |
| **MINOR** | Nuevas funcionalidades (backward compatible) | 1.0.0 → 1.1.0 |
| **PATCH** | Correcciones de bugs | 1.0.0 → 1.0.1 |

### Tagging en Git:
```bash
# Ver tags actuales
git tag

# Crear tag para release
git tag -a v1.1.0 -m "Release v1.1.0: Integración de Stripe y reportes"

# Subir tag
git push origin v1.1.0

# O subir todos los tags
git push origin --tags
```

---

## 6. Buenas Prácticas del Equipo

### ✅ HACER:
- ✅ Commits pequeños y enfocados (una funcionalidad por commit)
- ✅ Escribir mensajes descriptivos
- ✅ Hacer PR antes de mergear a develop
- ✅ Esperar aprobación de al menos 1 revisor
- ✅ Actualizar README si hay cambios de estructura
- ✅ Ejecutar tests localmente antes de push
- ✅ Sincronizarse regularmente con develop (`git pull`)

### ❌ EVITAR:
- ❌ Commits gigantes con múltiples funcionalidades
- ❌ Mensajes de commit vagas ("fix", "update", "wip")
- ❌ Commitear directamente a main o develop
- ❌ Mergear sin PR
- ❌ Mezclar feature con fixes críticos en mismo commit
- ❌ Olvidar pull antes de push (puede causar conflictos)
- ❌ Dejar commits sin pushear por días

---

## 7. Comandos Útiles Rápidos

```bash
# Ver estado actual
git status

# Ver últimos commits
git log --oneline -10

# Ver commits en una rama
git log feature/mi-rama --oneline

# Ver diferencias antes de commit
git diff

# Ver diferencias de una rama específica
git diff develop feature/mi-rama

# Cambiar de rama
git checkout develop

# Ver todas las ramas
git branch -a

# Obtener cambios remotos sin mergear
git fetch origin

# Sincronizar con develop (sin mergear la rama actual)
git rebase origin/develop

# Ver quién hizo cambios en una línea
git blame archivo.py

# Deshacer último commit (sin perder cambios)
git reset --soft HEAD~1

# Deshacer último commit (PERDIENDO cambios)
git reset --hard HEAD~1
```

---

## 8. Troubleshooting

### Problema: "conflict during merge"

```bash
# Ver archivos en conflicto
git status

# Editar archivos (buscar <<<<<<, ======, >>>>>>)
# Luego:
git add .
git commit -m "merge: resolver conflictos"
```

### Problema: "feature muy vieja, mucho atrás de develop"

```bash
# Actualizar feature con cambios de develop
git checkout feature/mi-rama
git rebase origin/develop

# O si hay conflictos complejos:
git merge origin/develop
```

### Problema: "Olvidé cambiar de rama y commitee en develop"

```bash
# Deshacer commit pero guardar cambios
git reset --soft HEAD~1

# Cambiar a feature
git checkout -b feature/nombre

# Committear correctamente
git add .
git commit -m "feat: descripción"
```

### Problema: "Quiero deshacer un cambio local sin commitear"

```bash
# Ver qué cambió
git diff

# Descartar cambios (CUIDADO)
git checkout -- archivo.py

# O descartar todo
git reset --hard HEAD
```

---

## 9. Checklist Antes de Pushear

```
Antes de hacer git push, verificar:

□ git status limpio (nothing to commit)
□ Todos los cambios relacionados están en staging
□ Mensaje de commit describe bien los cambios
□ Tests locales pasan: pytest
□ Linting sin errores: flake8 .
□ No hay conflictos: git pull origin develop
□ README actualizado si hay cambios de estructura
□ No estoy en main ni develop
□ La rama tiene nombre descriptivo (feature/xxx)
```

---

## 10. Referencias Rápidas

- **Git Docs**: https://git-scm.com/doc
- **GitHub Flow**: https://guides.github.com/introduction/flow/
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Semantic Versioning**: https://semver.org/
- **PEP8 Style Guide**: https://pep8.org/

---

**Para cualquier duda sobre el flujo, referirse a este documento o consultar al Lead del proyecto.**

Última revisión: Marzo 2026
