# Frontend Development - Quick Cheat Sheet

## Your Setup ✅

**You:** Frontend (React) on `http://localhost:3000`  
**Backend:** Django in Docker on `http://localhost:8000`  
**Database:** PostgreSQL in Docker on `localhost:5432`  
**Cache:** Redis in Docker on `localhost:6379`

---

## 🚀 Start Your Day

### Terminal 1: Start Backend (Once)
```bash
# From project root
docker-compose -f docker-compose-dev.yaml up -d

# Check it's running
docker ps
```

### Terminal 2: Start Frontend (Every dev session)
```bash
# Navigate to frontend
cd src/frontend

# First time only: Install dependencies
npm install

# Start development server
npm start

# Opens: http://localhost:3000
```

---

## 📝 Key Files

| File | Location | Purpose |
|------|----------|---------|
| React App | `src/frontend/src/App.js` | Main component |
| Components | `src/frontend/src/components/` | Reusable UI |
| Pages | `src/frontend/src/pages/` | Route pages |
| Styles | `src/frontend/styles.css` | Global CSS |
| Config | `src/frontend/.env` | API URL & settings |
| Package | `src/frontend/package.json` | Dependencies |

---

## 🔌 API Connection

### Already Configured ✅

`src/frontend/.env` has:
```
REACT_APP_API_URL=http://localhost:8000/api
```

### Use in Code

```javascript
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL;

// GET example
axios.get(`${API_URL}/events/`)

// POST example
axios.post(`${API_URL}/events/`, { title: 'New Event' })
```

---

## 📊 Available Backend APIs

Backend runs on `http://localhost:8000/api/`

**Main Endpoints:**
```
GET    /api/events/           - List events
POST   /api/events/           - Create event
GET    /api/units/            - List units
POST   /api/units/            - Create unit
GET    /api/users/            - List users
POST   /api/users/            - Create user
GET    /api/enrollments/      - List enrollments
GET    /api/tickets/          - List tickets
```

---

## 🛠️ Common Commands

### Frontend

```bash
cd src/frontend

# Install dependencies (first time)
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Backend (in Docker)

```bash
# View logs
docker logs -f cos40005_backend

# Stop all containers
docker-compose -f docker-compose-dev.yaml down

# Restart backend
docker-compose -f docker-compose-dev.yaml restart backend

# Access backend shell
docker exec -it cos40005_backend bash
```

---

## 🐛 Debugging

### Frontend Issues

```
Browser Console (F12):
├─ Network tab    - Check API calls
├─ Console tab    - Check errors
└─ React tab      - Inspect components
```

### Backend Not Responding?

```bash
# 1. Check if running
docker ps

# 2. Test connection
curl http://localhost:8000/api/

# 3. View logs
docker logs cos40005_backend

# 4. Restart
docker-compose -f docker-compose-dev.yaml restart backend
```

### Port Already in Use?

```bash
# Port 3000 (frontend):
# Kill process using port
# Or use: PORT=3001 npm start

# Port 8000, 5432, 6379 (backend):
# Restart Docker: docker-compose down && docker-compose up -d
```

---

## 📦 Dependencies Available

You have these packages ready:

| Package | Use |
|---------|-----|
| **React** | UI framework |
| **React Router** | Navigation |
| **Material-UI (MUI)** | Components |
| **Axios** | HTTP requests |
| **Formik + Yup** | Forms & validation |
| **FullCalendar** | Calendar widget |
| **Emotion** | CSS styling |

---

## 💡 Example: Fetch and Display Data

```javascript
import { useEffect, useState } from 'react';
import axios from 'axios';

function MyComponent() {
  const [data, setData] = useState([]);
  const API_URL = process.env.REACT_APP_API_URL;

  useEffect(() => {
    // Call backend when component mounts
    axios.get(`${API_URL}/events/`)
      .then(res => setData(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      {data.map(item => (
        <div key={item.id}>{item.title}</div>
      ))}
    </div>
  );
}

export default MyComponent;
```

---

## 🎯 Development Workflow

### 1. Make Changes
```bash
# Edit files in src/frontend/src/
# Browser auto-refreshes
```

### 2. Test API
```bash
# Browser Console (F12)
# Network tab shows API calls
# Check if response is correct
```

### 3. Check Backend Logs
```bash
# Another terminal:
docker logs -f cos40005_backend
```

### 4. Commit When Done
```bash
git add .
git commit -m "Your changes"
```

---

## ⚠️ Common Issues & Fixes

### Issue: Blank page / 404 error
**Fix:** Backend not running
```bash
docker-compose -f docker-compose-dev.yaml up -d
```

### Issue: API calls failing (Network tab shows 404/500)
**Fix:** Check backend logs
```bash
docker logs cos40005_backend
```

### Issue: CORS error in console
**Fix:** Backend CORS already enabled, check API URL in .env
```bash
cat src/frontend/.env
```

### Issue: npm install stuck
**Fix:** Clear cache
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

## 🎓 Project Structure

```
src/frontend/
├── public/              - Static files (index.html)
├── src/
│   ├── components/      - Reusable components
│   ├── pages/           - Page components
│   ├── App.js           - Main app
│   └── index.js         - Entry point
├── styles.css           - Global styles
├── package.json         - Dependencies
├── .env                 - Configuration (API URL)
└── README.md            - React app docs
```

---

## ✅ Your Daily Checklist

- [ ] Backend containers running (`docker ps`)
- [ ] Frontend `npm start` executed
- [ ] Browser shows app at `http://localhost:3000`
- [ ] Network tab shows successful API calls
- [ ] Console shows no errors

---

## 🔗 Quick Links

| Resource | Location |
|----------|----------|
| Frontend Guide | FRONTEND_SETUP.md |
| Full Migration Guide | POSTGRESQL_MIGRATION_GUIDE.md |
| Backend API Docs | http://localhost:8000/api/ (when running) |
| React Docs | https://react.dev |
| MUI Docs | https://mui.com |

---

## 🎉 You're Ready!

```bash
# 1. Start backend (once)
docker-compose -f docker-compose-dev.yaml up -d

# 2. Start frontend (every session)
cd src/frontend && npm start

# 3. Open browser
http://localhost:3000

# 4. Start developing! 🚀
```

---

**Questions?** Check `FRONTEND_SETUP.md` for detailed guide.
