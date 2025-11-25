#!/bin/bash
# Initialize production database with proper user and permissions

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Initializing PostgreSQL database for production${NC}"

# This script is run inside the PostgreSQL container
# It creates the application user with appropriate permissions

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create application user if it doesn't exist
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'swin_cms') THEN
            CREATE USER swin_cms WITH ENCRYPTED PASSWORD '${POSTGRES_PASSWORD}';
        END IF;
    END
    \$\$;

    -- Grant connection privileges
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO swin_cms;
    GRANT USAGE ON SCHEMA public TO swin_cms;

    -- Grant table privileges
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO swin_cms;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO swin_cms;
    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO swin_cms;

    -- Set default privileges for future objects
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO swin_cms;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO swin_cms;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO swin_cms;

    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

EOSQL

echo -e "${GREEN}Database initialization completed successfully!${NC}"
