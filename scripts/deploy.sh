#!/bin/bash
# Deploy production environment
# This script handles the complete deployment process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env.prod"
COMPOSE_FILE="$PROJECT_DIR/docker-compose-prod.yaml"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     COS40005-CMS Production Deployment Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/6]${NC} Checking prerequisites..."

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ Missing .env.prod file${NC}"
    echo "Please copy .env.example.prod to .env.prod and update with your values"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose not found${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ docker not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Stop existing containers
echo -e "${YELLOW}[2/6]${NC} Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Build images
echo -e "${YELLOW}[3/6]${NC} Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build --no-cache
echo -e "${GREEN}✓ Images built successfully${NC}"
echo ""

# Start services
echo -e "${YELLOW}[4/6]${NC} Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Wait for database
echo -e "${YELLOW}[5/6]${NC} Waiting for database to be ready..."
WAIT_TIME=0
while [ $WAIT_TIME -lt 60 ]; do
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is ready${NC}"
        break
    fi
    sleep 2
    WAIT_TIME=$((WAIT_TIME + 2))
done

if [ $WAIT_TIME -ge 60 ]; then
    echo -e "${RED}✗ Database failed to start${NC}"
    exit 1
fi
echo ""

# Run migrations
echo -e "${YELLOW}[6/6]${NC} Running database migrations..."
docker-compose -f "$COMPOSE_FILE" exec -T backend python manage.py migrate
echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Deployment Completed Successfully!           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. Create a superuser: docker-compose exec backend python manage.py createsuperuser"
echo "  2. Verify application: curl https://your-domain"
echo "  3. Check logs: docker-compose logs -f backend"
echo ""
