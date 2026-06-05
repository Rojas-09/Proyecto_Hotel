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
git pull origin Development

# Crear feature branch
git checkout -b feature/mi-funcionalidad
```

---

## 3️⃣ DURANTE EL DESARROLLO

```bash
# Ver cambios realizados
git diff

# Ver cambios de un archivo específico
git diff app/controllers/reserva_controller.py

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

---

## 5️⃣ SINCRONIZACIÓN

```bash
# Subir cambios
git push origin feature/mi-funcionalidad

# Primera vez (establecer upstream)
git push -u origin feature/mi-funcionalidad

# Traer cambios nuevos
git pull origin Development

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
git checkout Development

# Crear y cambiar a nueva rama
git checkout -b feature/puntos-fidelidad

# Borrar rama local
git branch -d feature/rama-vieja

# Borrar rama remota
git push origin --delete feature/rama-vieja
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
git blame app/models/pago.py
```

---

## 8️⃣ DESHACER CAMBIOS

```bash
# Descartar cambios de un archivo (⚠️ DESTRUCTIVO)
git checkout -- app/controllers/auth_controller.py

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

## 9️⃣ COMANDOS URGENTES

```bash
# "¡Cambié algo sin querer!"
git checkout -- app/models/reserva.py

# "¡Hice commit en rama equivocada!"
git reset --soft HEAD~1
git checkout -b feature/correcta

# "¡Conflicto!"
git status              # Ver archivos conflictivos
# Editar manualmente archivos
git add .
git commit -m "merge: resolver conflictos"

# "¿Qué hay en Development?"
git log Development --oneline -10

# "¿Qué cambios tengo sin subir?"
git log origin/Development..HEAD --oneline

# "¡Las pruebas fallaron!"
pytest tests/ -q --no-cov-on-fail   # Correr tests rápido

# "¿El linting?"
flake8 app/ --max-line-length=100 --select=E,F
```

---

## 📖 DOCUMENTACIÓN OFICIAL

- **Git Docs**: https://git-scm.com/doc
- **GitHub Help**: https://docs.github.com
- **Conventional Commits**: https://www.conventionalcommits.org/
- **Repositorio**: https://github.com/Rojas-09/Proyecto_Hotel

---

**Guardar este archivo como referencia rápida. ¡Úsalo cuando tengas dudas! 📌**
