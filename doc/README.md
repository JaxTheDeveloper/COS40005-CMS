# COS40005-CMS

Up-to-date developer instructions for running the backend (Django) and frontend (React) locally.

## Quick overview

### Available User Accounts

The system comes with pre-configured test accounts for different user roles:

1. **Student Account**
   - Email: `student@swin.edu.au`
   - Password: `Test@123`
   - Access: Course enrollment, unit resources, queries

2. **Unit Convenor Account**
   - Email: `convenor@swin.edu.au`
   - Password: `Test@123`
   - Access: Unit management, reports, resource management

3. **Staff/Admin Account**
   - Email: `staff@swin.edu.au`
   - Password: `Test@123`
   - Access: Full administrative access

### Server URLs

- Backend (Django): http://localhost:8000
- Frontend (React dev server): http://localhost:3000
- PostgreSQL (Docker): localhost:5432
- Redis (Docker): localhost:6379
- PgAdmin (Docker): http://localhost:5050

> This repository includes a `docker-compose-dev.yaml` that runs PostgreSQL, Redis, and the Django backend in development mode. The React frontend is run separately (npm) so you get hot-reload.

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- Docker & Docker Compose

## Start services (non-blocking / development)

1) Start Docker-backed services (Postgres, Redis, and the Django container) in detached mode:

```powershell
docker-compose -f docker-compose-dev.yaml up --build -d
```

This will start containers and map ports from the compose file (Django on 8000, Postgres 5432, Redis 6379, pgAdmin 5050).

2) Start the frontend in a separate terminal (PowerShell). From project root:

```powershell
cd src\frontend
npm install
npm start
```

Notes:
- `npm start` (react-scripts) runs the dev server on port 3000 by default. If port 3000 is taken, it will prompt to use another port.
- Run the frontend in a separate terminal so both front and back run concurrently (non-blocking).

## MCP Server (Agentation tools)

A lightweight HTTP process exposes CMS actions to the Agentation widget used
in development. It is implemented in `tools/mcp_server.py` and can be started
either manually or via Docker Compose.

To run alongside the rest of your stack:

```powershell
docker-compose -f docker-compose-dev.yaml up -d mcp
```

Or launch directly in the backend container/venv:

```powershell
python tools/mcp_server.py
```

The server listens on port **8001** and provides endpoints such as
`/get_student_profile` and `/award_social_gold`. See `doc/MCP_SERVER.md` for
full documentation.

## Running backend tests (inside the backend container)

You can run Django tests using docker exec against the running backend container. Example (runs tests defined in the users app):

```powershell
docker exec -it cos40005_backend python manage.py test src.backend.users.tests.test_auth_and_profile -v 2
```

## Creating Test Users

To create test users (student, unit convenor, and staff accounts):

```powershell
docker exec -it cos40005_backend python manage.py create_test_users
```

This will create the test accounts listed at the top of this README.

## Authentication

For detailed information about authentication and user access:
- See [Authentication Documentation](doc/authentication.md)
- Default test accounts are provided for quick testing
- JWT tokens are used for API authentication
- Frontend automatically handles token management

## Troubleshooting

### Authentication Issues

1. **Login Not Working**
   - Ensure both backend and frontend are running
   - Check that you're using the correct email/password
   - Clear browser localStorage and try again

2. **API Access Denied**
   - Token might be expired - try logging out and back in
   - Check that you have the correct permissions for the endpoint

3. **404 Not Found Errors**
   - Verify that all services are running
   - Check the API endpoint URLs in the error message
   - Ensure you're logged in with appropriate permissions

Or run the full test suite:

```powershell
docker exec -it cos40005_backend python manage.py test -v 2
```

## Stopping services

- Stop and remove containers (Docker Compose):

```powershell
docker-compose -f docker-compose-dev.yaml down
```

- Stop and remove containers + volumes (reset DB):

```powershell
docker-compose -f docker-compose-dev.yaml down -v
```

- To stop the frontend dev server, press Ctrl+C in the terminal where `npm start` is running.

## Backend (local, without Docker)

If you prefer to run Django locally (not via the container):

```powershell
cd src\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

## Frontend production build

To create a production build of the frontend and serve it from any static server:

```powershell
cd src\frontend
npm run build
# then serve the build directory with your preferred static server
```

If you would like to serve the React build from Django in production, we can add a small integration step (collect static, configure WhiteNoise or a web server). Ask me and I can add it.

## API endpoints (examples)

- List enrollments (current user): `GET http://localhost:8000/api/enrollment/enrollments/`
- Create enrollment: `POST http://localhost:8000/api/enrollment/enrollments/` (body: { "offering": <id> })
- Social gold balance: `GET http://localhost:8000/api/social/social-gold/`

## Troubleshooting

- If a port is in use, stop the conflicting service or change the port.
- If Docker containers fail to start, check the logs:

```powershell
docker-compose -f docker-compose-dev.yaml logs backend
docker-compose -f docker-compose-dev.yaml logs postgres
```

- If frontend dependencies cause issues, remove `node_modules` and reinstall:

```powershell
cd src\frontend
rm -r node_modules
npm install
```
