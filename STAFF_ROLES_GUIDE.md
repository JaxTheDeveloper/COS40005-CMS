# Staff Roles & Accounts - User Guide

## Role Types in the System

There's a clear distinction between **HQ Staff** and **Unit Convenors**:

### 1. **HQ Staff** (`user_type='staff'`)
- **Purpose**: Administrative staff at headquarters
- **Scope**: System-wide access
- **Responsibilities**:
  - Manage organization-wide events
  - Broadcast messages to all units
  - Access system-wide analytics
  - Create and manage CSV import workflows
  
**Demo Account**:
- Email: `staff@swin.edu.au`
- Password: `password`
- Role Badge: "HQ Staff"

---

### 2. **Unit Convenor** (`user_type='unit_convenor'`)
- **Purpose**: Academic staff in charge of a specific unit/course
- **Scope**: Unit-level access
- **Responsibilities**:
  - Manage unit-specific events
  - Create and assign instructors for sessions
  - Mark student attendance
  - Send notifications to enrolled students
  - Refine event content for their unit
  
**Demo Account**:
- Email: `convenor@swin.edu.au`
- Password: `password`
- Unit: `DEMO101` (Introduction to Demo)
- Role Badge: "Unit Convenor"

---

### 3. **Administrator** (`user_type='admin'`)
- **Purpose**: System administrator
- **Scope**: Full system access
- **Permissions**: All HQ Staff + Unit Convenor permissions
- Role Badge: "Administrator"

---

## Demo Accounts Created by Seeder

When you run:
```bash
docker exec -it cos40005_backend python manage.py seed_student_demo refresh
```

The following accounts are created:

| Account | Email | Password | Role | Permissions |
|---------|-------|----------|------|-------------|
| HQ Staff | `staff@swin.edu.au` | `password` | HQ Staff | System-wide event management |
| Unit Convenor | `convenor@swin.edu.au` | `password` | Unit Convenor | DEMO101 management |
| Demo Student 1-5 | `demo_student_N@example.com` | `password` | Student | View enrollments & notifications |

---

## Accessing Staff Event Manager

Both HQ Staff and Unit Convenors can access `/staff/events`, but the interface shows their role:

### For HQ Staff (`staff@swin.edu.au`)
1. Login to the system
2. Click **"Staff Events"** in sidebar (visible because `is_staff=True`)
3. Badge shows: **"HQ Staff"**
4. Can upload/manage organization-wide events

### For Unit Convenor (`convenor@swin.edu.au`)
1. Login to the system
2. Click **"Staff Events"** in sidebar (visible because `is_staff=True`)
3. Badge shows: **"Unit Convenor"**
4. Can upload/manage unit-specific events
5. Can also access **"Teaching"** dashboard (see class attendance)

---

## Permissions Matrix

| Feature | Student | Unit Convenor | HQ Staff | Admin |
|---------|---------|---------------|----------|-------|
| View public events | ✅ | ✅ | ✅ | ✅ |
| View private events (unit-scoped) | If enrolled | ✅ | ❌ | ✅ |
| Upload CSV events | ❌ | ✅ | ✅ | ✅ |
| Edit/refine event content | ❌ | ✅ | ✅ | ✅ |
| Manage student attendance | ❌ | ✅ (own unit) | ❌ | ✅ |
| Send notifications | ❌ | ✅ (own students) | ✅ (all) | ✅ |
| Access Teaching Dashboard | ❌ | ✅ | ❌ | ✅ |
| View system admin panel | ❌ | ❌ | ✅ | ✅ |

---

## Testing Different Roles

### Test as Unit Convenor
```bash
# Login with
Email: convenor@swin.edu.au
Password: password

# You'll see:
- Dashboard (general)
- Calendar
- Enrolment
- Notifications
- Teaching (shows DEMO101 attendance data)
- Staff Events (can upload/manage CSV)
- Profile
```

### Test as HQ Staff
```bash
# Login with
Email: staff@swin.edu.au
Password: password

# You'll see:
- Dashboard (general)
- Calendar
- Enrolment
- Notifications
- Staff Events (can upload/manage CSV)
- Profile

# Note: You won't see "Teaching" (unit-specific)
```

### Test as Student
```bash
# Login with
Email: demo_student_1@example.com
Password: password

# You'll see:
- Dashboard
- Calendar
- Enrolment
- Notifications (shows seeded notifications)
- Profile

# You won't see:
- Teaching (student, not staff)
- Staff Events (student, not staff)
```

---

## How Backend Checks Permissions

### Staff Event Manager (`/staff/events`)
```javascript
// Component checks:
const isAuthorized = user?.is_staff || 
  ['staff', 'unit_convenor', 'admin'].includes(user?.user_type);

if (!isAuthorized) {
  return <Alert>Access Denied</Alert>;
}
```

### CSV Import Endpoint (`POST /api/events/import-csv/`)
```python
# Backend checks:
permission_classes = [IsStaff]  # Django staff flag OR is_staff=True
```

---

## User Type Field in Database

The `user_type` field in the User model has these options:
- `'student'` - Regular student
- `'staff'` - HQ/Administrative staff
- `'unit_convenor'` - Academic department staff (unit-level)
- `'auditor'` - Auditor
- `'parent'` - Parent/Guardian
- `'admin'` - Administrator

The `is_staff` Django flag is set to `True` for all staff-like roles to enable admin access.

---

## Modifying Demo Credentials

To change demo account passwords or emails, edit the seeder:

```python
# File: src/backend/enrollment/management/commands/seed_student_demo.py

# HQ Staff account
staff_email = 'staff@swin.edu.au'  # Change email here
# Or change user_type: 'staff' to 'admin'

# Unit Convenor account
convenor_email = 'convenor@swin.edu.au'  # Change email here
# Or change user_type: 'unit_convenor' to 'admin'
```

Then re-run:
```bash
docker exec -it cos40005_backend python manage.py seed_student_demo refresh
```
