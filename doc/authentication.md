## Authentication and Access

### First-Time Setup

1. Start all services (see "Start services" section below)
2. Open the frontend application at `http://localhost:3000`
3. Click "Login" and use one of the test accounts listed above

### Available Features by Role

#### Student Features
- View and enroll in available units
- Access unit resources and materials
- Submit queries and questions
- Track academic progress
- Use AI assistance for learning

#### Unit Convenor Features
- Manage unit content and resources
- View and generate reports
- Respond to student queries
- Monitor unit performance

#### Staff/Admin Features
- Full system administration
- User management
- Course and unit setup
- System configuration

### JWT Authentication

The system uses JWT (JSON Web Token) authentication:
- Tokens are automatically managed by the frontend
- Access tokens expire after 5 minutes
- Refresh tokens are valid for 24 hours
- Automatic token refresh is handled by the frontend

### API Endpoints

Key API endpoints for authentication:

```
POST /api/token/
- Get JWT tokens with email/password
- Returns: access and refresh tokens

POST /api/token/refresh/
- Refresh expired access token
- Requires: valid refresh token

GET /api/users/users/me/
- Get current user profile
- Requires: valid access token
```

For API development, you can test endpoints using curl:

```powershell
# Get JWT token
curl -X POST http://localhost:8000/api/token/ -H "Content-Type: application/json" -d "{\"email\":\"student@swin.edu.au\",\"password\":\"Test@123\"}"

# Access protected endpoint
curl http://localhost:8000/api/users/users/me/ -H "Authorization: Bearer <your-token>"
```