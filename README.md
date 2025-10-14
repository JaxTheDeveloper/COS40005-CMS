# ECPS 

## Project Structure

```
ECPS/
├── ecps_backend/          # Django REST API backend
│   ├── manage.py
│   ├── requirements.txt
│   └── ecps_backend/
├── ecps-frontend/         # React TypeScript frontend
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
├── docker-compose-dev.yaml # Development Docker services
└── README.md
```

## Prerequisites

Before running this project, make sure you have the following installed:

- **Python 3.8+** (for Django backend)
- **Node.js 16+** and **npm** (for React frontend)
- **Docker and Docker Compose** (for database and services)
- **Git** (for version control)

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd .....
```

### 2. Environment Setup

Create a `.env` file in the project root with the following variables:

```env
# Database Configuration
DB_NAME=construction
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# PostgreSQL Docker Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=construction

# PgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin
```

### 3. Start Database Services

Start PostgreSQL, Redis, and PgAdmin using Docker Compose:

```bash
docker-compose -f docker-compose-dev.yaml up -d
```

This will start:
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`
- **PgAdmin** on port `5050` (accessible at http://localhost:5050)

### 4. Backend Setup (Django)

Navigate to the backend directory:

```bash
cd ecps_backend
```

#### Create and activate a virtual environment:

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

#### Install Python dependencies:

```bash
pip install -r requirements.txt
```

#### Run database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Create a superuser (optional):

```bash
python manage.py createsuperuser
```

#### Start the Django development server:

```bash
python manage.py runserver
```

The backend API will be available at: http://localhost:8000

### 5. Frontend Setup (React)

Open a new terminal and navigate to the frontend directory:

```bash
cd ecps-frontend
```

#### Install Node.js dependencies:

```bash
npm install
```

#### Start the development server:

```bash
npm run dev
```

The frontend will be available at: http://localhost:5173

## Available Services

Once everything is running, you can access:

- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **PgAdmin**: http://localhost:5050
- **API Documentation**: http://localhost:8000/api/ (if configured)

## Development Workflow

### Backend Development

1. **Activate virtual environment**: `.\venv\Scripts\Activate.ps1` (Windows) or `source venv/bin/activate` (macOS/Linux)
2. **Make model changes**: Edit models in Django apps
3. **Create migrations**: `python manage.py makemigrations`
4. **Apply migrations**: `python manage.py migrate`
5. **Run tests**: `python manage.py test`

### Frontend Development

1. **Start development server**: `npm run dev`
2. **Run linting**: `npm run lint`
3. **Build for production**: `npm run build`
4. **Preview production build**: `npm run preview`

## Technology Stack

### Backend
- **Django 5.1.4** - Web framework
- **Django REST Framework 3.14.0** - API framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **JWT** - Authentication
- **CORS** - Cross-origin resource sharing

### Frontend
- **React 19.1.0** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **ESLint** - Code linting

### Infrastructure
- **Docker** - Containerization
- **PostgreSQL** - Database
- **Redis** - Caching
- **PgAdmin** - Database administration

## Environment Variables

The application uses the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_NAME` | Database name | `construction` |
| `DB_USER` | Database username | `postgres` |
| `DB_PASSWORD` | Database password | `password` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |

## Troubleshooting

### Common Issues

1. **Port already in use**: Make sure no other services are running on ports 5432, 5173, 8000, or 5050
2. **Database connection error**: Ensure Docker services are running with `docker-compose ps`
3. **Python virtual environment**: Always activate the virtual environment before running Django commands
4. **Node modules**: Delete `node_modules` and run `npm install` if you encounter dependency issues

### Useful Commands

**Check Docker services:**
```bash
docker-compose -f docker-compose-dev.yaml ps
```

**View Docker logs:**
```bash
docker-compose -f docker-compose-dev.yaml logs postgres
```

**Stop all Docker services:**
```bash
docker-compose -f docker-compose-dev.yaml down
```

**Reset database:**
```bash
docker-compose -f docker-compose-dev.yaml down -v
docker-compose -f docker-compose-dev.yaml up -d
```