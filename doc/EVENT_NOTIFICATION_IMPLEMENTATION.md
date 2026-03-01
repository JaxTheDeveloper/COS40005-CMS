# Event & Notification System Implementation

## Overview
Successfully implemented a comprehensive event and notification system with staff CMS capabilities and student-facing notification views, with proper role distinction between HQ Staff and Unit Convenors.

## Backend Enhancements

### 1. Updated Seeder Command with Role Distinction
**File**: `src/backend/enrollment/management/commands/seed_student_demo.py`
- Creates **Unit Convenor** account (`convenor@swin.edu.au`, `user_type='unit_convenor'`)
  - Academic department staff for DEMO101 unit
  - Can manage unit-specific events and attendance
  - Has access to Teaching Dashboard
  
- Creates **HQ Staff** account (`staff@swin.edu.au`, `user_type='staff'`)
  - Administrative headquarters staff
  - Can manage organization-wide events
  - No unit-specific dashboard

- Adds `Notification` import and creation
- Seeds 15 demo notifications (3 per student: attendance_marked, fees_due, event_created)
- Properly tracks notifications in `demo_seed.json` for safe refresh/cleanup

**Run**:
```bash
docker exec -it cos40005_backend python manage.py seed_student_demo refresh
```

**Result**: 
- Creates convenor (unit_convenor), HQ staff, 5 demo students
- Creates demo unit (DEMO101), 5 weekly sessions, 5 enrollments
- Seeds 25 attendance records, 15 notifications

### 2. Event API Endpoints (Already Implemented)
- `POST /api/events/import-csv/` - Staff uploads CSV file, forwards to n8n webhook
- `PUT /api/events/{id}/refine_content/` - Staff updates event.generated_content, generation_status, generation_meta

### 3. Notification Model & ViewSet (Already Implemented)
- `NotificationViewSet` provides CRUD operations at `/api/notifications/`
- Filters notifications by recipient (current user)
- Supports mark as read via PATCH

### 4. Enrollment Status Notifications (New)
Staff actions that change a student's enrollment now trigger a notification record:

- A Django signal (`post_save`) on `Enrollment` watches for status transitions
  to **ENROLLED** or **WITHDRAWN** (including when created in that state).
- When detected, a `Notification` is created for the `Enrollment.student` with
  the verb set to `'Enrollment enrolled'` or `'Enrollment withdrawn'` and the
  enrollment instance as the `target`.
- This addresses *Gap 4* from the review: previously approvals did not inform
  students.

No database migration was required since the notification model already existed.

Example test coverage can be found in `src/backend/enrollment/tests.py`.

### 5. Student-to-Staff Messaging (New)
Students can now compose and send arbitrary messages to administrative staff
or unit convenors directly from the notifications page:

- The `/notifications` page renders a **"Send Message"** button which toggles
  a simple form.
- Recipients are restricted to users with `user_type` of `staff`,
  `unit_convenor` or `admin`.  The backend enforces this rule with serializer
  validation.
- When sent, the notification appears in the recipient's notifications feed and
  is visible to staff when they visit the same `/notifications` route.
- Staff and students both use the same page; the form is only shown when a user
  has at least one eligible recipient (i.e. not for staff-only accounts).

API behaviour:
```http
POST /api/core/notifications/
{
  "recipient": 5,
  "verb": "question",
  "description": "Can I get an extension?"
}
```

Server-side safeguards include:
- Queryset filtering so users only see notifications addressed to them.
- `perform_create` sets `actor` to the sender.
- Serializer rejects student→student messages.

See the new tests under `src/backend/core/tests.py` for examples.

### 6. Enrollment Request Alerts (New)
When a student submits a new enrollment (which starts in **PENDING** status),
staff are now automatically alerted:

- A post‑save signal on `Enrollment` picks up newly created records with
  `status='PENDING'`.
- Notifications are sent to:
  1. the **unit convenor** of the offering (if one exists) and
  2. all users with `is_staff=True`.
- The verb used is `'Enrollment pending approval'` and the target is the
  enrollment instance itself.

This ensures that the people responsible for approving enrollments can see
requests in their notification feed without manually polling the dashboard.

The behaviour is covered by new tests in
`src/backend/enrollment/tests.py` and requires no additional database
schema changes.  It completes the approval workflow by closing the loop on
student registrations.


## Frontend Implementation

### 1. Staff Event Manager Page
**File**: `src/frontend/src/pages/StaffEventManager.jsx`
- **Route**: `/staff/events`
- **Access Control**: Checks for `is_staff=True` or `user_type` in `['staff', 'unit_convenor', 'admin']`
- **Role Display**: Shows badge with "HQ Staff", "Unit Convenor", or "Administrator"
- **Features**:
  - CSV Import Tab: Upload CSV file to forward to n8n webhook
  - Manage Events Tab: List all events with edit/generate buttons
  - Event Editor Dialog: Refine event content (JSON editor), change generation_status
  - Notifications Tab: Placeholder for notification management (coming soon)
- **Permissions**: Staff-only (checked via API)
- **API Integration**:
  - Loads events: `GET /api/core/events/`
  - Upload CSV: `POST /api/core/events/import-csv/`
  - Save refined content: `PUT /api/core/events/{id}/refine_content/`

### 2. Student Notifications Page
**File**: `src/frontend/src/pages/StudentNotifications.jsx`
- **Route**: `/notifications`
- **Features**:
  - Unified view of notifications and private events
  - Filter by: All, Unread notifications, Events, Notifications
  - Notifications show: type icon, verb, description, timestamp, mark-as-read button
  - Events show: title, description, start time, location, visibility badge
  - Dismiss individual notifications/events
- **Permissions**: All authenticated users
- **API Integration**:
  - Loads private events: `GET /api/core/events/` (filters visibility != 'public')
  - Loads notifications: `GET /api/core/notifications/`
  - Mark as read: `PATCH /api/core/notifications/{id}/` with `unread: false`

### 3. Updated Routes in App.jsx
- Added import for `StaffEventManager` and `StudentNotifications`
- Registered new routes:
  - `/staff/events` → StaffEventManager
  - `/notifications` → StudentNotifications

### 4. Updated Sidebar Navigation
**File**: `src/frontend/src/components/Sidebar.jsx`
- Added "Notifications" link for all users (appears in menu for everyone)
- Added "Staff Events" link for staff/unit_convenor/admin users
- Menu structure:
  - Dashboard
  - Calendar
  - Enrolment
  - **Notifications** (new, visible to all)
  - Teaching (staff only)
  - **Staff Events** (new, staff only)
  - Profile

## Event Model Fields (Already Implemented)
```python
class Event(UnitAwareModel):
    # Content
    title = CharField(max_length=255)
    description = TextField(blank=True)
    start = DateTimeField()
    end = DateTimeField(null=True)
    location = CharField(blank=True)
    
    # Visibility Control
    visibility = CharField(choices=['public', 'unit', 'staff'], default='public')
    related_unit = ForeignKey(Unit, null=True)
    related_offering = ForeignKey(SemesterOffering, null=True)
    attendees = ManyToManyField(User)
    
    # Content Generation (n8n Integration)
    generated_content = JSONField()  # {social_post, email_newsletter, article, ad}
    generation_status = CharField(choices=['idle', 'pending', 'ready', 'failed'])
    generation_meta = JSONField()    # {tone, brand_score, bias_flag, source}
```

## Notification Model Fields
```python
class Notification(Model):
    recipient = ForeignKey(User)
    actor = ForeignKey(User, null=True)
    verb = CharField(max_length=200)  # e.g., 'attendance_marked', 'fees_due', 'event_created'
    target = GenericForeignKey()      # Can target any model
    unread = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
```

## Demo Data After Seeding

When you run `docker exec -it cos40005_backend python manage.py seed_student_demo refresh`:

**Staff Accounts Created**:
- **Unit Convenor**: `convenor@swin.edu.au` (password: `password`)
  - `user_type='unit_convenor'`
  - Manages DEMO101 unit
  - Can see Teaching Dashboard
  - Can upload/manage events
  
- **HQ Staff**: `staff@swin.edu.au` (password: `password`)
  - `user_type='staff'`
  - System-wide access
  - Can upload/manage organization-wide events
  - Cannot see unit-specific Teaching Dashboard

**Demo Students**:
- 5× `demo_student_N@example.com` (password: `password`)
- All enrolled in DEMO101 offering

**Academic Objects**:
- Unit: `DEMO101` - Introduction to Demo (Convenor: `convenor@swin.edu.au`)
- SemesterOffering: Current year/semester S1
- 5 Weekly Sessions (Lectures, Mon 09:00-10:30)

**Enrollment Objects**:
- 5 Enrollments (all 5 students enrolled in offering)
- 25 AttendanceRecords (weighted: 80% present, 10% late, 8% absent, 2% excused)

**Notifications** (NEW):
- 15 Notifications total (3 per student):
  1. `attendance_marked` - Notification that attendance was recorded
  2. `fees_due` - Payment reminder notification
  3. `event_created` - Event notification announcement

All created IDs are tracked in `data/demo_seed.json` for safe cleanup on next refresh.

## Testing the Implementation

### Backend
```bash
# Run seeder
docker exec -it cos40005_backend python manage.py seed_student_demo refresh

# Check notifications endpoint
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/core/notifications/

# Check events endpoint
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/core/events/
```

### Frontend
1. Login as `convenor@swin.edu.au` / `password`
2. Click "Staff Events" in sidebar
   - Upload a CSV file with event data
   - View/edit event content
3. Click "Notifications" to see notifications & private events
   - View 15 demo notifications created by seeder
   - Mark notifications as read
4. Login as `demo_student_1@example.com` / `password`
   - View "Notifications" page (shows assigned notifications)
   - See unit-scoped events if created with visibility='unit'

## Next Steps (Optional Enhancements)

1. **N8N Workflow Setup**: Configure n8n webhook to:
   - Process CSV imports and create Event records
   - Generate content using LLM/Claude API
   - Send notifications to students

2. **Event Filtering**: Add filtering in StudentNotifications to show only:
   - Events in user's enrolled units
   - Events where user is in related_unit

3. **Bulk Notifications**: Add endpoint to send notifications to students based on criteria (e.g., all students in unit, by status)

4. **Email Integration**: Use Celery/background tasks to send email notifications

5. **Real-time Updates**: Add WebSocket support for live notification updates

## Files Modified

1. `src/backend/enrollment/management/commands/seed_student_demo.py` - Added notification seeding
2. `src/backend/core/views_api.py` - Added import_csv and refine_content actions (already done)
3. `src/frontend/src/pages/StaffEventManager.jsx` - NEW
4. `src/frontend/src/pages/StudentNotifications.jsx` - NEW
5. `src/frontend/src/App.jsx` - Added routes
6. `src/frontend/src/components/Sidebar.jsx` - Added navigation links

## Compilation Status
✅ Frontend compiles successfully without errors
✅ Seeder runs successfully with notification creation
✅ Backend API endpoints ready for use
