#!/bin/bash
# Database backup script
# Usage: ./scripts/backup-database.sh

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-SwinCMS}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_HOST:-localhost}"
CONTAINER_NAME="${CONTAINER_NAME:-cos40005_postgres_prod}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting database backup at $(date)"
echo "Database: $DB_NAME"
echo "Backup directory: $BACKUP_DIR"

# Perform backup
BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${TIMESTAMP}.sql"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "${BACKUP_FILE}.gz"

if [ $? -eq 0 ]; then
    echo "✓ Backup completed successfully: ${BACKUP_FILE}.gz"
    ls -lh "${BACKUP_FILE}.gz"
else
    echo "✗ Backup failed!"
    exit 1
fi

# Keep only last 30 backups
echo "Cleaning up old backups (keeping last 30)..."
find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -type f -printf '%T+ %p\n' | sort -r | tail -n +31 | cut -d' ' -f2- | xargs -r rm

echo "Backup completed at $(date)"
