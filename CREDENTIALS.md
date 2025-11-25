# COS40005-CMS Demo Credentials

## Staff Accounts

### Unit Convenor (Academic Department)
```
Email:    convenor@swin.edu.au
Password: password
Role:     Unit Convenor
Type:     unit_convenor
Unit:     DEMO101
```

### HQ Staff (Administrative)
```
Email:    staff@swin.edu.au
Password: password
Role:     HQ Staff
Type:     staff
Unit:     None (organization-wide)
```

## Student Accounts

### Demo Students (5 accounts)
```
Email:    demo_student_1@example.com through demo_student_5@example.com
Password: password (all)
Role:     Student
Status:   ENROLLED in DEMO101
```

### Individual Student Accounts
- demo_student_1@example.com / password
- demo_student_2@example.com / password
- demo_student_3@example.com / password
- demo_student_4@example.com / password
- demo_student_5@example.com / password

## Demo Unit

```
Unit Code:     DEMO101
Unit Name:     Introduction to Demo
Convenor:      convenor@swin.edu.au
Year:          2024
Semester:      S1
Enrolled:      5 students
Sessions:      5 weekly lectures (Mon 09:00-10:30)
```

## API Endpoints

### Authentication
- Login: `POST /api/token/compat/` - Use email + password
- Refresh: `POST /api/token/refresh/` - Use refresh token
- Current User: `GET /api/users/me/` - Get authenticated user

### Events
- List: `GET /api/core/events/`
- Create: `POST /api/core/events/`
- Import CSV: `POST /api/core/events/import-csv/` (Staff only)
- Refine: `PUT /api/core/events/{id}/refine_content/` (Staff only)

### Notifications
- List: `GET /api/core/notifications/`
- Mark Read: `PATCH /api/core/notifications/{id}/`

### Enrollment
- Dashboard: `GET /api/enrollment/enrollments/dashboard/` (Students)
- Teaching: `GET /api/enrollment/enrollments/teaching/` (Staff/Convenors)

## Frontend URLs

```
Login:                http://localhost:3000/login
Dashboard:            http://localhost:3000/dashboard/compsci
Enrollments:          http://localhost:3000/enrol/select
Teaching Dashboard:   http://localhost:3000/teaching (Convenors only)
Staff Events:         http://localhost:3000/staff/events (Staff only)
Notifications:        http://localhost:3000/notifications
Calendar:             http://localhost:3000/calendar
Profile:              http://localhost:3000/profile
```

## N8N Integration

### CSV Import Webhook
```
URL: https://conditionally-brimful-exie.ngrok-free.dev/webhook-test/import-schedule
Method: POST
Format: CSV file forwarded from /api/events/import-csv/
```

## Important Notes

- **Password**: All demo accounts use the same password: `password`
- **Demo Data**: Created via `docker exec -it cos40005_backend python manage.py seed_student_demo refresh`
- **Notifications**: 15 seeded notifications (3 per student)
- **Attendance**: 25 records (5 students × 5 sessions)
- **Seed Tracking**: All created IDs stored in `data/demo_seed.json`

## Development Setup

### Backend
```bash
docker-compose -f docker-compose-dev.yaml up -d
docker exec -it cos40005_backend python manage.py seed_student_demo refresh
```

### Frontend
```bash
cd src/frontend
npm start
```

### Rebuild Demo Data
```bash
docker exec -it cos40005_backend python manage.py seed_student_demo refresh
```

## Testing Scenarios

### Test as Unit Convenor
1. Login: `convenor@swin.edu.au` / `password`
2. View Teaching Dashboard (attendance analytics)
3. Upload/manage events via Staff Events page
4. See "Teaching" link in sidebar

### Test as HQ Staff
1. Login: `staff@swin.edu.au` / `password`
2. Upload/manage organization-wide events
3. No "Teaching" link in sidebar
4. Same Staff Events interface as convenor

### Test as Student
1. Login: `demo_student_1@example.com` / `password`
2. View enrollments
3. View 3 seeded notifications
4. No staff features visible

## Generated Data Summary

| Item | Count | Details |
|------|-------|---------|
| Users | 7 | 2 staff + 5 students |
| Units | 1 | DEMO101 |
| Offerings | 1 | S1 2024 |
| Sessions | 5 | Weekly lectures |
| Enrollments | 5 | All students in DEMO101 |
| Attendance | 25 | 5 × 5 sessions |
| Notifications | 15 | 3 per student |

---

**Last Generated**: November 25, 2025
**Status**: Active - All credentials functional
