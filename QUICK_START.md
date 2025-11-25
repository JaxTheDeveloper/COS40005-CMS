# Quick Start - Demo Accounts & Testing

## Available Demo Accounts

### **Unit Convenor** (Academic Department)
```
Email:    convenor@swin.edu.au
Password: password
Role:     Unit Convenor
Unit:     DEMO101 (Introduction to Demo)
```
**Can do**:
- View Teaching Dashboard (attendance analytics)
- Upload/manage events for DEMO101
- Mark student attendance
- Access Staff Events page
- Send notifications to students

---

### **HQ Staff** (Administrative)
```
Email:    staff@swin.edu.au
Password: password
Role:     HQ Staff
Unit:     None (organization-wide)
```
**Can do**:
- Upload/manage organization-wide events
- Access Staff Events page
- (Expand permissions as needed)

---

### **Demo Students** (5 accounts)
```
Email:    demo_student_1@example.com  (through 5)
Password: password (all)
Role:     Student
Status:   ENROLLED in DEMO101
```
**Can do**:
- View enrollments
- View notifications (15 seeded notifications)
- View unit events
- See attendance data for their own sessions

---

## How to Test

### Setup (One-time)
```bash
# 1. Start backend
docker-compose -f docker-compose-dev.yaml up -d

# 2. Seed demo data
docker exec -it cos40005_backend python manage.py seed_student_demo refresh

# 3. Start frontend
cd src/frontend && npm start
```

### Test as Unit Convenor
1. Go to http://localhost:3000
2. Login with `convenor@swin.edu.au` / `password`
3. Click **"Teaching"** in sidebar → See attendance dashboard
4. Click **"Staff Events"** → Upload CSV or manage events
5. Badge shows: **"Unit Convenor"**

### Test as HQ Staff
1. Go to http://localhost:3000
2. Login with `staff@swin.edu.au` / `password`
3. Click **"Staff Events"** → Same interface
4. Badge shows: **"HQ Staff"** (different from convenor)
5. Note: **No "Teaching" link** (not unit-specific)

### Test as Student
1. Go to http://localhost:3000
2. Login with `demo_student_1@example.com` / `password`
3. Click **"Notifications"** → See 3 seeded notifications
4. Click **"Enrolment"** → See DEMO101 enrollment
5. Note: **No "Staff Events"** or **"Teaching"** links

---

## Demo Data Quick Summary

| Item | Count | Details |
|------|-------|---------|
| Units | 1 | DEMO101 |
| Semester Offerings | 1 | S1 2024 |
| Sessions | 5 | Mon 09:00-10:30 (Weeks 1-5) |
| Enrolled Students | 5 | demo_student_1 through 5 |
| Attendance Records | 25 | 5 students × 5 sessions |
| Notifications | 15 | 3 per student |
| Instructors | 1 | convenor (unit_convenor) |

---

## Key Differences: Convenor vs HQ Staff

| Feature | Convenor | HQ Staff |
|---------|----------|----------|
| **user_type** | `'unit_convenor'` | `'staff'` |
| Teaching Dashboard | ✅ Yes | ❌ No |
| Staff Events | ✅ Yes | ✅ Yes |
| Unit Assignment | ✅ DEMO101 | ❌ None |
| Scope | Single unit | Organization-wide |
| Sidebar Items | 7 (includes Teaching) | 6 (no Teaching) |

---

## Useful Commands

### Refresh Demo Data (Clears and Recreates)
```bash
docker exec -it cos40005_backend python manage.py seed_student_demo refresh
```

### Seed (Add Demo Data, Don't Clear)
```bash
docker exec -it cos40005_backend python manage.py seed_student_demo seed
```

### View Django Shell
```bash
docker exec -it cos40005_backend python manage.py shell
```

### Create Superuser
```bash
docker exec -it cos40005_backend python manage.py createsuperuser
```

### View Demo Seed Record
```bash
# Linux/Mac
cat data/demo_seed.json

# Windows PowerShell
Get-Content data/demo_seed.json
```

---

## Troubleshooting

### "Access Denied" on Staff Events Page
- Make sure you're logged in as `convenor@swin.edu.au` or `staff@swin.edu.au`
- These are the only accounts with `is_staff=True`

### No "Teaching" Dashboard Link
- You're logged in as HQ Staff (`staff@swin.edu.au`)
- Only Unit Convenors see this link
- Try logging in as `convenor@swin.edu.au`

### No "Staff Events" Link
- You're logged in as a student
- Staff Events requires `is_staff=True`

### Notifications Not Showing
- Run seeder refresh: `docker exec -it cos40005_backend python manage.py seed_student_demo refresh`
- Login as `demo_student_1@example.com`
- Go to `/notifications`

### API Errors
- Check backend logs: `docker logs cos40005_backend`
- Verify API is running: `curl http://localhost:8000/api/users/me/`
- Check auth token is saved in localStorage

---

## Next Steps

1. **Configure N8N webhook** for CSV import automation
2. **Create event visibility rules** (who can see which events)
3. **Add bulk notification sending** (send to all students in unit)
4. **Setup email integration** (send emails via Gmail API)
5. **Add real-time updates** (WebSockets for live notifications)

---

## API Endpoints Quick Reference

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/users/me/` | GET | Token | Get current user |
| `/api/core/events/` | GET/POST | Token | List/create events |
| `/api/core/events/import-csv/` | POST | Staff | Upload CSV |
| `/api/core/events/{id}/refine_content/` | PUT | Staff | Update event content |
| `/api/core/notifications/` | GET/PATCH | Token | List/mark notifications |
| `/api/enrollment/enrollments/teaching/` | GET | Staff | Teaching dashboard |
| `/api/token/compat/` | POST | None | Login (email/password) |

---

## Files Modified in This Session

1. ✅ `src/backend/enrollment/management/commands/seed_student_demo.py` - Added HQ staff + notifications
2. ✅ `src/frontend/src/pages/StaffEventManager.jsx` - Added role display + access control
3. ✅ `src/frontend/src/pages/StudentNotifications.jsx` - Student notifications view
4. ✅ `src/frontend/src/App.jsx` - Added routes
5. ✅ `src/frontend/src/components/Sidebar.jsx` - Role-based nav
6. ✅ `STAFF_ROLES_GUIDE.md` - Detailed role documentation
7. ✅ `EVENT_NOTIFICATION_IMPLEMENTATION.md` - Updated with role distinction

---

**Last Updated**: November 25, 2025
**Frontend Status**: ✅ Compiles successfully
**Backend Status**: ✅ Seeder runs successfully
