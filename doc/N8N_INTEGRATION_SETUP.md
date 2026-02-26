# N8N Integration Setup - Complete

## Changes Made

### 1. **docker-compose-dev.yaml** ✅
Added n8n service to development environment:
- Image: `n8n/n8n:latest`
- Port: `5678` (accessible at `http://localhost:5678`)
- PostgreSQL backend for workflow storage
- Persistent volume: `n8n_data`
- Same Docker network as backend (`postgres` network)

### 2. **docker-compose-prod.yaml** ✅
Added n8n service to production environment:
- Image: `n8n/n8n:latest`
- Environment variables from `.env` for configuration
- Exposed only internally (no external port)
- PostgreSQL backend for workflow storage
- Persistent volume: `n8n_data`
- Same Docker network as backend (`backend` network)

### 3. **config/settings/dev.py** ✅
Updated webhook configuration:
```python
N8N_IMPORT_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/import-schedule'
N8N_API_KEY = None
N8N_WEBHOOK_SECRET = None
```

### 4. **config/settings/prod.py** ✅
Added n8n configuration for production:
```python
N8N_IMPORT_WEBHOOK = os.environ.get('N8N_IMPORT_WEBHOOK', 'http://cos40005_n8n_prod:5678/webhook-test/import-schedule')
N8N_API_KEY = os.environ.get('N8N_API_KEY')
N8N_WEBHOOK_SECRET = os.environ.get('N8N_WEBHOOK_SECRET')
```

---

## How It Works Now

```
Frontend (React)
    ↓
Backend (Django) on cos40005_backend
    ↓
CSV Upload: POST /api/events/import-csv/
    ↓
Django forwards to: http://cos40005_n8n:5678/webhook-test/import-schedule
    ↓
N8N processes, generates content, enriches data
    ↓
N8N calls back: POST /api/events/batch-create-webhook/
    ↓
Events stored in PostgreSQL with generated_content JSONB
```

---

## Starting the System

### Development

```bash
# Start all services (PostgreSQL, Redis, Backend, n8n, pgAdmin)
docker-compose -f docker-compose-dev.yaml up -d

# View n8n UI
Open: http://localhost:5678
```

### Production

```bash
# Build and start (requires .env.prod with proper credentials)
docker-compose -f docker-compose-prod.yaml up -d --build

# View logs
docker-compose -f docker-compose-prod.yaml logs -f
```

---

## Key URLs

### Development
- **Backend API**: http://localhost:8000
- **N8N UI**: http://localhost:5678
- **pgAdmin**: http://localhost:5050
- **Redis**: localhost:6379

### Production
- **Backend API**: https://yourdomain.com (via nginx)
- **N8N**: Internal only (not exposed externally)

---

## Network Communication

Both docker-compose files use a single Docker network (`postgres` in dev, `backend` in prod), allowing containers to communicate via container names:

- `cos40005_backend` → `cos40005_n8n` ✅ (backend initiates)
- `cos40005_n8n` → `cos40005_backend` ✅ (n8n calls webhook)

No external URLs needed for inter-service communication.

---

## Environment Variables (Production)

Add these to `.env.prod`:

```bash
# N8N Configuration (optional - defaults to Docker network URL)
N8N_IMPORT_WEBHOOK=http://cos40005_n8n_prod:5678/webhook-test/import-schedule
N8N_API_KEY=<your-api-key-if-needed>
N8N_WEBHOOK_SECRET=<your-webhook-secret-if-needed>
N8N_HOST=cos40005_n8n_prod
```

---

## Testing the Integration

### 1. Create a test CSV file
```csv
title,description,start,end,location,visibility
New Event,Test event,2025-02-01T10:00:00Z,2025-02-01T11:00:00Z,Room A,public
```

### 2. Upload via API
```bash
curl -X POST http://localhost:8000/api/events/import-csv/ \
  -H "Authorization: Bearer <your-token>" \
  -F "file=@test.csv"
```

### 3. Check N8N logs
```bash
docker logs -f cos40005_n8n
```

### 4. Verify events created
```bash
curl http://localhost:8000/api/events/ \
  -H "Authorization: Bearer <your-token>"
```

---

## Database Setup for N8N

N8N will automatically create its own database schema in PostgreSQL:
- Database: `n8n` (created automatically)
- User: `postgres`
- Host: `cos40005_postgres` (dev) or from env (prod)

If the database doesn't exist, n8n will create it on first run.

---

## Next Steps

1. **Start Docker Desktop** (if not running)
2. **Run**: `docker-compose -f docker-compose-dev.yaml up -d`
3. **Access N8N**: http://localhost:5678
4. **Create n8n workflow** for:
   - Receiving CSV imports
   - Parsing and validating data
   - Calling LLM (Claude, GPT) for content generation
   - Posting back to `/api/events/batch-create-webhook/`

---

## Architecture Benefits

✅ **Decoupled**: N8N runs independently  
✅ **Scalable**: Can run N8N on separate server in production  
✅ **Reliable**: Docker network ensures stable communication  
✅ **Persistent**: Volumes preserve data across container restarts  
✅ **Isolated**: Each service has its own database/resources  
✅ **Secure**: Internal network for service-to-service communication  

---

## Troubleshooting

### N8N won't start
```bash
# Check logs
docker logs cos40005_n8n

# Verify PostgreSQL is healthy
docker exec cos40005_postgres pg_isready -U postgres
```

### Webhook calls failing
```bash
# From backend container, test connectivity to n8n
docker exec cos40005_backend curl http://cos40005_n8n:5678/health

# Check n8n is listening
docker exec cos40005_n8n curl http://localhost:5678/health
```

### Database issues
```bash
# Check n8n database was created
docker exec cos40005_postgres psql -U postgres -l | grep n8n

# If missing, create it
docker exec cos40005_postgres psql -U postgres -c "CREATE DATABASE n8n;"
```

---

## Files Modified

1. [docker-compose-dev.yaml](docker-compose-dev.yaml)
2. [docker-compose-prod.yaml](docker-compose-prod.yaml)
3. [config/settings/dev.py](config/settings/dev.py)
4. [config/settings/prod.py](config/settings/prod.py)
