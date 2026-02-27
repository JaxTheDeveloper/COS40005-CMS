# Frontend Setup Guide - Running Separately from Backend

**Your Understanding is Correct!** ✅

The backend runs as a separate Docker container, and you only need to run the frontend locally.

---

## Architecture

```
Your Development Machine
├─ Frontend (React)
│  ├─ Port: 3000
│  ├─ Location: src/frontend/
│  └─ Command: npm start
│
└─ Calls via HTTP/CORS
        ↓
Docker Backend
├─ Backend (Django)
│  ├─ Port: 8000
│  ├─ Container: cos40005_backend
│  └─ Command: python manage.py runserver
│
├─ Database (PostgreSQL)
│  ├─ Port: 5432
│  └─ Container: cos40005_postgres
│
└─ Cache (Redis)
   ├─ Port: 6379
   └─ Container: cos40005_redis
```

---

## Quick Start

### Step 1: Start Backend Containers (One Time)

```bash
# From project root
docker-compose -f docker-compose-dev.yaml up -d

# Verify containers are running
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE          NAMES
...            postgres:...   cos40005_postgres
...            redis:...      cos40005_redis
...            (backend)      cos40005_backend
```

### Step 2: Start Frontend Locally

```bash
# Navigate to frontend directory
cd src/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

### Step 3: Access Application

Open browser to: **http://localhost:3000**

---

## Environment Setup

### Prerequisites

- ✅ Node.js 14+ (for npm)
- ✅ Docker & Docker Compose (for backend)
- ✅ Port 3000 available (frontend)
- ✅ Port 8000 available (backend)

### Check Versions

```bash
# Check Node.js
node --version
npm --version

# Check Docker
docker --version
docker-compose --version
```

---

## Frontend Development

### Install Dependencies

```bash
cd src/frontend
npm install
```

### Available Scripts

```bash
# Start development server (auto-reload)
npm start

# Build for production
npm run build

# Run tests
npm test

# Eject configuration (NOT RECOMMENDED)
npm run eject
```

### Development Server Features

- ✅ Hot reload on file changes
- ✅ CORS proxy to backend (if configured)
- ✅ Console errors and warnings displayed
- ✅ Default browser opening on port 3000

---

## Connecting Frontend to Backend

### Frontend API Configuration

Check `src/frontend/src/` for API calls. They should use:

```javascript
// Correct - Uses relative path (respects CORS proxy)
const API_URL = 'http://localhost:8000/api';
axios.get(`${API_URL}/events/`);

// Or environment variable
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

### Create `.env` in Frontend Directory

```bash
# src/frontend/.env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_API_TIMEOUT=30000
```

### CORS Configuration (Backend Already Set)

The backend is already configured with CORS in development:

```python
# config/settings/dev.py
CORS_ALLOW_ALL_ORIGINS = True
```

✅ Frontend can freely call backend APIs without CORS issues

---

## Common Development Workflow

### Morning Startup

```bash
# 1. Start backend containers (from project root)
docker-compose -f docker-compose-dev.yaml up -d

# 2. Open new terminal and start frontend
cd src/frontend
npm start

# 3. Browser opens to http://localhost:3000
# Frontend auto-reloads on file changes
```

### Making Changes

```bash
# Edit React files in src/frontend/src/
# Browser automatically refreshes

# Edit Django code in src/backend/
# Django dev server auto-reloads
```

### Checking Backend Logs

```bash
# In another terminal
docker logs -f cos40005_backend
```

### Stopping Everything

```bash
# Stop frontend: Ctrl+C in terminal

# Stop backend containers
docker-compose -f docker-compose-dev.yaml down

# Or keep running and use next day
```

---

## Troubleshooting

### Issue: Frontend won't connect to backend

**Solution:**
```bash
# 1. Check backend is running
docker ps | grep backend

# 2. Test backend directly
curl http://localhost:8000/api/

# 3. Check frontend is using correct API URL
# Look in src/frontend/.env or code for REACT_APP_API_URL
```

### Issue: Port 3000 already in use

**Solution:**
```bash
# Find process using port 3000
lsof -i :3000  # Mac/Linux
netstat -ano | findstr :3000  # Windows

# Kill the process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows

# Or change port
PORT=3001 npm start
```

### Issue: npm install fails

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Issue: Backend not responding

**Solution:**
```bash
# Check containers are running
docker ps

# Restart containers
docker-compose -f docker-compose-dev.yaml restart

# Check logs
docker logs cos40005_backend

# Verify backend is healthy
curl http://localhost:8000/api/
```

---

## Development Tips

### 1. Use React DevTools
```bash
# Install Chrome extension
# React DevTools
# Redux DevTools (if using Redux)
```

### 2. Browser Console
- Open: F12 or Ctrl+Shift+I
- Tab: Console
- View network requests, errors, warnings

### 3. Network Debugging
```javascript
// Add to frontend code to see API calls
axios.interceptors.request.use(request => {
  console.log('Starting Request:', request);
  return request;
});

axios.interceptors.response.use(response => {
  console.log('Response:', response);
  return response;
});
```

### 4. Backend Debugging
```bash
# SSH into container
docker exec -it cos40005_backend /bin/bash

# Check migrations
python manage.py showmigrations

# Run Django shell
python manage.py shell
```

---

## Project Structure

```
COS40005-CMS/
├── src/
│   ├── frontend/              ← YOU RUN THIS (npm start)
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── App.js
│   │   │   └── index.js
│   │   ├── package.json
│   │   └── .env              ← Create this with API URL
│   │
│   └── backend/               ← RUNS IN DOCKER
│       ├── users/
│       ├── academic/
│       ├── core/
│       └── manage.py
│
├── docker-compose-dev.yaml    ← Backend containers
├── Dockerfile.dev
└── [Other files]
```

---

## Frontend Features Available

Based on `package.json`, you have:

- ✅ **React 18** - UI framework
- ✅ **Material-UI (MUI)** - Component library
- ✅ **React Router** - Navigation
- ✅ **Axios** - HTTP client
- ✅ **Formik + Yup** - Form handling & validation
- ✅ **FullCalendar** - Calendar component
- ✅ **Emotion** - CSS-in-JS styling

---

## Example: Making an API Call

### In Your React Component

```javascript
import axios from 'axios';
import { useEffect, useState } from 'react';

function EventsList() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  useEffect(() => {
    // Call backend API
    axios.get(`${API_URL}/events/`)
      .then(response => {
        setEvents(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching events:', error);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      {events.map(event => (
        <div key={event.id}>{event.title}</div>
      ))}
    </div>
  );
}

export default EventsList;
```

### Backend Will Respond With

```json
[
  {
    "id": 1,
    "title": "Event Title",
    "description": "Description",
    "start": "2025-11-25T10:00:00Z",
    "end": "2025-11-25T11:00:00Z",
    "location": "Room 101",
    ...
  }
]
```

---

## Daily Workflow

### Start of Day
```bash
# Terminal 1: Start backend
docker-compose -f docker-compose-dev.yaml up -d

# Terminal 2: Start frontend
cd src/frontend
npm start

# Browser opens to http://localhost:3000
```

### During Development
```bash
# Edit React code in src/frontend/src/
# Refresh browser automatically (hot reload)

# Edit Django code in src/backend/
# Django reloads automatically

# Check backend logs in Terminal 1
docker logs -f cos40005_backend
```

### End of Day
```bash
# Stop frontend: Ctrl+C

# Optional: Stop backend
docker-compose -f docker-compose-dev.yaml down

# Or keep running for tomorrow
```

---

## Next Steps

1. ✅ Ensure backend containers are running: `docker-compose -f docker-compose-dev.yaml up -d`
2. ✅ Navigate to frontend: `cd src/frontend`
3. ✅ Create `.env` file with API URL
4. ✅ Install dependencies: `npm install`
5. ✅ Start frontend: `npm start`
6. ✅ Open http://localhost:3000

---

## Questions?

### Backend Issues
- Check: POSTGRESQL_MIGRATION_GUIDE.md
- Logs: `docker logs cos40005_backend`

### Frontend Issues
- Check: src/frontend/README.md
- Logs: Browser console (F12)

### API Connection Issues
- Verify backend running: `curl http://localhost:8000/api/`
- Check API URL in frontend `.env`
- Check CORS in Django settings

---

**You're all set! Just run the frontend while backend containers handle the heavy lifting.** 🚀
