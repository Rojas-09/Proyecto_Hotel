#!/bin/sh
set -e

if [ ! -d "/app/migrations/versions" ]; then
    echo "Inicializando migraciones..."
    flask db init
fi

if [ -z "$(ls -A /app/migrations/versions/ 2>/dev/null)" ]; then
    echo "Creando migración inicial..."
    flask db migrate -m "initial"
fi

echo "Ejecutando migraciones..."
flask db upgrade

echo "Iniciando Gunicorn..."
exec gunicorn -w 4 -b 0.0.0.0:5000 run:app --access-logfile - --error-logfile - --timeout 120
