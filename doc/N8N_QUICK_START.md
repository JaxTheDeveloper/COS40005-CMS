# N8N + Backend Setup - Quick Start

## ✅ What Was Done

Your n8n integration has been configured to run in the same Docker network as your backend. This solves the container communication issue.

### Configuration Updates:
- ✅ Added `n8n` service to `docker-compose-dev.yaml`
- ✅ Added `n8n` service to `docker-compose-prod.yaml`
- ✅ Updated `N8N_IMPORT_WEBHOOK` URL in both settings
- ✅ Created persistent volumes for n8n data

---

## 🚀 Getting Started

### Start Docker Desktop First
Make sure Docker Desktop is running on your Windows machine.

### Start All Services (Development)

```bash
cd D:\Work\COS40005-CMS

# Start all containers
docker-compose -f docker-compose-dev.yaml up -d

# Verify all services started
docker-compose -f docker-compose-dev.yaml ps
```

### Access the Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Backend API** | http://localhost:8000 | - |
| **N8N UI** | http://localhost:5678 | (create account on first login) |
| **pgAdmin** | http://localhost:5050 | admin@admin.com / admin |
| **PostgreSQL** | localhost:5432 | postgres / password |

---

## 📋 Key Files Modified

```
config/
  settings/
    dev.py          ← N8N_IMPORT_WEBHOOK updated
    prod.py         ← N8N_IMPORT_WEBHOOK added

docker-compose-dev.yaml   ← n8n service added
docker-compose-prod.yaml  ← n8n service added
```

---

## 🔧 How Backend & N8N Communicate

### Event CSV Import Workflow

1. **User** uploads CSV → `POST /api/events/import-csv/`
2. **Backend** forwards file → `http://cos40005_n8n:5678/webhook-test/import-schedule`
   - Uses Docker internal network (no external URL needed)
   - Container name resolution automatically works
3. **N8N** processes CSV
   - Parses data
   - Calls LLM for content generation (optional)
   - Validates output
4. **N8N** posts back → `POST /api/events/batch-create-webhook/`
5. **Backend** stores events in PostgreSQL

---

## 🎯 What to Do Next

### 1. Create n8n Workflow
Log into http://localhost:5678 and create a workflow that:
- Receives the webhook call from backend
- Parses CSV data
- Generates marketing content (optional: via Claude/OpenAI)
- Posts results back to Django

### 2. Test the Integration
```bash
# Upload a test CSV
curl -X POST http://localhost:8000/api/events/import-csv/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@events.csv"

# Check n8n logs
docker logs -f cos40005_n8n
```

### 3. Verify Database
```bash
# Connect to PostgreSQL
docker exec -it cos40005_postgres psql -U postgres -d SwinCMS

# Check events were created
SELECT id, title, generation_status FROM core_event LIMIT 5;
```

---

## 💾 Rebuilding Backend (with Database Changes)

```bash
# This automatically runs migrations
docker-compose -f docker-compose-dev.yaml up -d --build backend

# Or manually
docker exec -it cos40005_backend python manage.py migrate
```

---

## 🔍 Common Commands

```bash
# View logs
docker-compose -f docker-compose-dev.yaml logs -f backend
docker-compose -f docker-compose-dev.yaml logs -f n8n

# Stop all services
docker-compose -f docker-compose-dev.yaml down

# Stop and remove volumes (WARNING: deletes data)
docker-compose -f docker-compose-dev.yaml down -v

# Restart a specific service
docker-compose -f docker-compose-dev.yaml restart backend

# Run Django command
docker exec -it cos40005_backend python manage.py migrate
docker exec -it cos40005_backend python manage.py shell
```

---

## 📚 Documentation

- Full setup details: [N8N_INTEGRATION_SETUP.md](N8N_INTEGRATION_SETUP.md)
- Backend architecture: [CODE_ARCHITECTURE_REVIEW.md](CODE_ARCHITECTURE_REVIEW.md)
- Event API docs: [EVENT_WORKFLOW_API.md](EVENT_WORKFLOW_API.md)
- Event generation: [src/backend/core/README_EVENTS_GENERATION.md](src/backend/core/README_EVENTS_GENERATION.md)

---

## ⚙️ Settings Reference

### Development (`config/settings/dev.py`)
```python
N8N_IMPORT_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/import-schedule'
N8N_API_KEY = None  # Set if n8n requires auth
N8N_WEBHOOK_SECRET = None  # Set for additional security
```

### Production (`config/settings/prod.py`)
```python
N8N_IMPORT_WEBHOOK = os.environ.get('N8N_IMPORT_WEBHOOK', 'http://cos40005_n8n_prod:5678/webhook-test/import-schedule')
N8N_API_KEY = os.environ.get('N8N_API_KEY')
N8N_WEBHOOK_SECRET = os.environ.get('N8N_WEBHOOK_SECRET')
```

Add to `.env.prod`:
```bash
N8N_IMPORT_WEBHOOK=http://cos40005_n8n_prod:5678/webhook-test/import-schedule
N8N_API_KEY=<your-api-key>  # optional
N8N_WEBHOOK_SECRET=<your-secret>  # optional
```

---

## 🐛 Troubleshooting

### N8N Container Won't Start
```bash
docker logs cos40005_n8n
# Common issues: PostgreSQL not running, permissions
```

### Backend Can't Reach N8N
```bash
# Test from backend container
docker exec cos40005_backend curl http://cos40005_n8n:5678/health

# If fails, check n8n is running
docker ps | grep n8n
```

### Database Issues
```bash
# Check n8n database exists
docker exec cos40005_postgres psql -U postgres -l | grep n8n

# If missing, n8n will create it on startup
```

---

## ✨ That's It!

Your system is now ready to:
- ✅ Accept CSV uploads via REST API
- ✅ Forward them to n8n for processing
- ✅ Receive generated content back
- ✅ Store everything in PostgreSQL
- ✅ Scale independently (backend ≠ n8n)

**Next: Start Docker Desktop and run `docker-compose -f docker-compose-dev.yaml up -d`**
