#!/bin/bash
# Django management commands for production
# Usage: ./scripts/manage.sh [command]

set -e

CONTAINER_NAME="${CONTAINER_NAME:-cos40005_backend_prod}"

# Colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

case "$1" in
    migrate)
        echo -e "${YELLOW}Running migrations...${NC}"
        docker exec "$CONTAINER_NAME" python manage.py migrate
        echo -e "${GREEN}✓ Migrations completed${NC}"
        ;;
    
    createsuperuser)
        echo -e "${YELLOW}Creating superuser...${NC}"
        docker exec -it "$CONTAINER_NAME" python manage.py createsuperuser
        ;;
    
    collectstatic)
        echo -e "${YELLOW}Collecting static files...${NC}"
        docker exec "$CONTAINER_NAME" python manage.py collectstatic --noinput
        echo -e "${GREEN}✓ Static files collected${NC}"
        ;;
    
    shell)
        echo -e "${YELLOW}Starting Django shell...${NC}"
        docker exec -it "$CONTAINER_NAME" python manage.py shell
        ;;
    
    dbshell)
        echo -e "${YELLOW}Starting database shell...${NC}"
        docker exec -it "$CONTAINER_NAME" python manage.py dbshell
        ;;
    
    makemigrations)
        echo -e "${YELLOW}Making migrations for $2...${NC}"
        docker exec "$CONTAINER_NAME" python manage.py makemigrations $2
        ;;
    
    logs)
        echo -e "${YELLOW}Tailing container logs...${NC}"
        docker logs -f "$CONTAINER_NAME"
        ;;
    
    bash)
        echo -e "${YELLOW}Starting container bash shell...${NC}"
        docker exec -it "$CONTAINER_NAME" /bin/bash
        ;;
    
    *)
        echo "Available commands:"
        echo "  migrate              - Run database migrations"
        echo "  createsuperuser      - Create a superuser"
        echo "  collectstatic        - Collect static files"
        echo "  shell                - Start Django shell"
        echo "  dbshell              - Start database shell"
        echo "  makemigrations [app] - Create migrations for app"
        echo "  logs                 - Tail container logs"
        echo "  bash                 - Start container bash"
        exit 1
        ;;
esac
