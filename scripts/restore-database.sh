#!/bin/bash
# Restore database from backup
# Usage: ./scripts/restore-database.sh [backup_file.gz]

set -e

BACKUP_DIR="./backups"
CONTAINER_NAME="${CONTAINER_NAME:-cos40005_postgres_prod}"
DB_NAME="${POSTGRES_DB:-SwinCMS}"
DB_USER="${POSTGRES_USER:-postgres}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${YELLOW}Available backups:${NC}"
    ls -lh "$BACKUP_DIR"/backup_*.sql.gz | awk '{print $9, "(" $5 ")"}'
    echo ""
    echo "Usage: $0 [backup_file.gz]"
    echo "Example: $0 backups/backup_SwinCMS_20240101_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Database Restore Procedure${NC}"
echo "Backup file: $BACKUP_FILE"
echo "Database: $DB_NAME"
echo ""
echo -e "${RED}⚠️  WARNING: This will overwrite all data in the database!${NC}"
read -p "Are you sure you want to continue? Type 'yes' to confirm: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "Terminating existing connections..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity 
     WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" 2>/dev/null || true

echo "Dropping existing database..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"

echo "Creating new database..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

echo "Restoring from backup..."
gunzip < "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database restore completed successfully!${NC}"
else
    echo -e "${RED}✗ Database restore failed!${NC}"
    exit 1
fi
