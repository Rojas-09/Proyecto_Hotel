# 🚀 QUICK REFERENCE - Comandos Git Esenciales

**HotelBook Pro - Guía Rápida de Comandos**

---

## 1️⃣ CONFIGURACIÓN INICIAL

```bash
# Configurar nombre y email (una sola vez)
git config --global user.name "Tu Nombre"
git config --global user.email "tu.email@utp.edu.co"

# Verificar configuración
git config --list

# Clonar el repositorio
git clone https://github.com/Rojas-09/Proyecto_Hotel.git
cd Proyecto_Hotel
```

---

## 2️⃣ INICIO DE CADA DÍA

```bash
# Verificar estado actual
git status

# Traer cambios nuevos
git pull origin develop

# Crear feature branch
git checkout -b feature/mi-funcionalidad
```

---

## 3️⃣ DURANTE EL DESARROLLO

```bash
# Ver cambios realizados
git diff

# Ver cambios de un archivo específico
git diff app/services/reserva_service.py

# Ver cambios staged
git diff --staged

# Preparar cambios (staging)
git add app/services/reserva_service.py    # Archivo específico
git add .                                   # Todos los cambios

# Ver qué está en staging
git status
```

---

## 4️⃣ COMMITEAR

```bash
# Commit simple
git commit -m "feat(reservas): agregar validación de fechas"

# Commit con descripción detallada (abre editor)
git commit

# Ammend (modificar último commit)
git commit --amend
```

### 📋 Tipos de Commits
```
feat:     Nueva funcionalidad
fix:      Corrección de bug
docs:     Documentación
refactor: Mejora de código
test:     Tests/Cobertura
chore:    Mantenimiento
style:    Formato (sin lógica)
```

---

## 5️⃣ SINCRONIZACIÓN

```bash
# Subir cambios
git push origin feature/mi-funcionalidad

# Primera vez (establecer upstream)
git push -u origin feature/mi-funcionalidad

# Traer cambios nuevos
git pull origin develop

# Ver cambios remotos sin mergear
git fetch origin
```

---

## 6️⃣ RAMAS

```bash
# Ver ramas locales
git branch

# Ver todas las ramas (local + remote)
git branch -a

# Cambiar de rama
git checkout develop

# Crear y cambiar a nueva rama
git checkout -b feature/nueva-rama

# Borrar rama local
git branch -d feature/vieja-rama

# Borrar rama remota
git push origin --delete feature/vieja-rama
```

---

## 7️⃣ HISTORIAL

```bash
# Ver últimos commits
git log --oneline -10

# Ver commits de una rama específica
git log feature/mi-rama --oneline

# Ver commits con detalles
git log -p -3

# Ver quien hizo qué en una línea
git blame app/models/reserva.py
```

---

## 8️⃣ DESHACER CAMBIOS

```bash
# Descartar cambios de un archivo (⚠️ DESTRUCTIVO)
git checkout -- app/models/reserva.py

# Descartar todos los cambios (⚠️ DESTRUCTIVO)
git reset --hard HEAD

# Deshacer último commit (guardar cambios)
git reset --soft HEAD~1

# Deshacer último commit (perder cambios)
git reset --hard HEAD~1

# Revertir un commit específico
git revert <commit-hash>
```

---

## 9️⃣ PULL REQUESTS & MERGE

```bash
# Mergear en local
git checkout develop
git pull origin develop
git merge feature/mi-rama
git push origin develop

# Ver cambios antes de mergear
git diff develop feature/mi-rama
```

---

## 🔟 TROUBLESHOOTING

### Conflictos en Merge
```bash
# Ver estado
git status

# Editar archivos con conflictos (buscar <<<<<<, ======, >>>>>>)
# Luego:
git add .
git commit -m "merge: resolver conflictos"
```

### Cambios por Accidente en Rama Equivocada
```bash
# Guardar cambios en stash
git stash

# Cambiar a rama correcta
git checkout feature/correcta

# Aplicar cambios
git stash pop
```

### Tu Rama Está Muy Atrás de develop
```bash
# Actualizar feature con cambios de develop
git checkout feature/mi-rama
git rebase origin/develop
```

### Olvidé Qué Rama Tenía
```bash
# Ver rama actual
git branch

# Mostrar más detalles
git status
```

---

## 🎯 WORKFLOW COMPLETO (Paso a Paso)

```bash
# 1. Empezar el día
git checkout develop
git pull origin develop

# 2. Crear feature
git checkout -b feature/validar-fechas

# 3. Desarrollar (editar archivos)
# ... editar app/services/reserva_service.py ...

# 4. Ver qué cambió
git status
git diff

# 5. Preparar commit
git add app/services/reserva_service.py

# 6. Commitear
git commit -m "feat(reservas): agregar validación de fechas

- Valida que fecha_salida > fecha_entrada
- Prohíbe reservas con menos de 24h
- Cubre 92% del código"

# 7. Subir a GitHub
git push -u origin feature/validar-fechas

# 8. En GitHub: Crear Pull Request
# - Base: develop
# - Compare: feature/validar-fechas
# - Escribir descripción
# - Hacer click en "Create Pull Request"

# 9. Esperar aprobación del revisor

# 10. Mergear en GitHub (o localmente)

# 11. Limpiar rama local
git checkout develop
git pull origin develop
git branch -d feature/validar-fechas
```

---

## 📊 REFERENCIA RÁPIDA DE ESTADOS

| Situación | Comando | Resultado |
|-----------|---------|-----------|
| ¿Dónde estoy? | `git status` | Muestra rama y cambios |
| Ver últimos cambios | `git log --oneline -5` | Últimos 5 commits |
| Ver diferencias | `git diff` | Cambios no staged |
| Cambiar de rama | `git checkout main` | Cambia a main |
| Traer cambios | `git pull` | Trae cambios de remoto |
| Subir cambios | `git push` | Sube cambios locales |
| Crear commit | `git commit -m "..."` | Crea snapshot |
| Ver ramas | `git branch -a` | Todas las ramas |

---

## 🔐 SEGURIDAD - NUNCA HAGAS

```bash
# ❌ NUNCA commitear directamente a main
git commit (mientras estés en main)

# ❌ NUNCA commitear directamente a develop
git commit (mientras estés en develop)

# ❌ NUNCA hacer git push sin pull antes
# (Siempre: git pull primero, luego git push)

# ❌ NUNCA usar git reset --hard sin saber qué haces
# (Es destructivo, no hay forma de recuperar)

# ❌ NUNCA commitear archivos sensibles
# .env, passwords, tokens
# (Configurar .gitignore para estos)
```

---

## 📋 CHECKLIST ANTES DE git push

```
🔍 Verificar:
□ Estoy en rama feature/xxx (no en main ni develop)
□ git status muestra los cambios que espero
□ Los tests pasan: pytest
□ No hay errores de linting: flake8 .
□ El commit tiene mensaje descriptivo
□ Tracé git pull antes (para evitar conflictos)
□ Tracé git status está limpio después del commit
```

---

## 🎓 EJEMPLOS DE USO REAL

### Ejemplo 1: Feature de Validación Rápida

```bash
# Iniciar
git checkout develop && git pull

# Crear feature
git checkout -b feature/validar-email

# Editar archivo
code app/services/usuario_service.py

# Commit
git add app/services/usuario_service.py
git commit -m "feat(usuario): validar formato de email"

# Subir
git push -u origin feature/validar-email
```

### Ejemplo 2: Corregir un Bug

```bash
# Cambiar a develop
git checkout develop && git pull

# Crear feature
git checkout -b fix/calcular-impuestos

# Editar
code app/services/factura_service.py

# Commit (nota: usar "fix" en lugar de "feat")
git add app/services/factura_service.py
git commit -m "fix(factura): corregir cálculo doble de IVA"

# Subir
git push -u origin fix/calcular-impuestos
```

### Ejemplo 3: Actualizar Tests

```bash
# Cambiar a develop
git checkout develop && git pull

# Crear feature
git checkout -b test/cobertura-reserva

# Editar
code tests/test_reserva.py

# Commit
git add tests/test_reserva.py
git commit -m "test(reserva): aumentar cobertura al 95%"

# Subir
git push -u origin test/cobertura-reserva
```

---

## 🔗 ESTRUCTURA DE URL DE RAMA CORRECTA

```bash
✅ CORRECTO - Nombres descriptivos:
   feature/validar-fechas-reserva
   feature/integrar-stripe
   fix/calcular-doble-iva
   test/cobertura-factura
   docs/actualizar-endpoints

❌ INCORRECTO - No descriptivo:
   feature/1
   fix/bug
   feature/wip
   test/test
   docs/update
```

---

## 📞 COMANDOS URGENTES

```bash
# "¡Cambié algo sin querer!"
git checkout -- archivo.py

# "¡Hice commit en rama equivocada!"
git reset --soft HEAD~1
git checkout -b feature/correcta

# "¡Conflicto!"
git status              # Ver archivos conflictivos
# Editar manualmente archivos
git add .
git commit -m "merge: resolver conflictos"

# "¿Qué hay en develop?"
git log develop --oneline -10

# "¿Qué cambios tengo sin subir?"
git log origin/develop..HEAD --oneline
```

---

## 📖 DOCUMENTACIÓN OFICIAL

- **Git Docs**: https://git-scm.com/doc
- **GitHub Help**: https://docs.github.com
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Git Cheat Sheet**: https://github.com/joshnh/Git-Commands

---

**Guardar este archivo como referencia rápida. ¡Úsalo cuando tengas dudas! 📌**
