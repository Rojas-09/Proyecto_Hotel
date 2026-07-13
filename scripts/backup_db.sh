#!/bin/bash
set -e

BACKUP_DIR="$HOME/backups/hotelbook"
PROJECT_DIR="$HOME/Documentos/Desarrollo/Hotel/Proyecto_Hotel"
TIMESTAMP=$(date +%Y%m%d_%H%M)
FILENAME="hotelbook_$TIMESTAMP.sql"
MAX_BACKUPS=14

mkdir -p "$BACKUP_DIR"

cd "$PROJECT_DIR"

docker compose exec -T db pg_dump -U hotelbook hotelbook > "$BACKUP_DIR/$FILENAME"

gzip "$BACKUP_DIR/$FILENAME"
echo "✅ Backup: $BACKUP_DIR/$FILENAME.gz ($(du -h "$BACKUP_DIR/$FILENAME.gz" | cut -f1))"

# Limpiar backups viejos (mayores a 14 días)
find "$BACKUP_DIR" -name "hotelbook_*.sql.gz" -mtime +$MAX_BACKUPS -delete
