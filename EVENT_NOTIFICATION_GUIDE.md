# Event & Notification System - User Guide

## For Students

### View Your Notifications
1. Click **"Notifications"** in the left sidebar
2. You'll see:
   - **Unread notifications** (attendance updates, fee reminders, event announcements)
   - **Private unit events** (events created by your unit convenor)
   - **Upcoming class sessions**

### Filter Notifications
Use the filter chips at the top:
- **All**: Shows everything
- **Unread**: Shows only unread notifications
- **Events**: Shows only upcoming events
- **Notifications**: Shows only system notifications (fees, attendance, etc.)

### Manage Notifications
- **Mark as read**: Click "Mark as read" button on unread notifications
- **Dismiss**: Click the X button to dismiss a notification or event

## For Staff/Convenors

### Access Staff Event Manager
1. Click **"Staff Events"** in the left sidebar (only visible to staff)
2. Three tabs available:
   - **CSV Import**: Upload event data
   - **Manage Events**: Edit/refine event content
   - **Notifications**: (Coming soon) Send notifications to students

### CSV Import Tab
1. Click **"Upload CSV"** button
2. Select your CSV file with columns: `title`, `description`, `start`, `end`, `location`, `visibility`, `related_unit_id`
3. File is forwarded to n8n webhook for processing
4. Example format:
   ```csv
   title,description,start,end,location,visibility,related_unit_id
   Guest Lecture,Industry expert talk,2024-03-15T14:00:00,2024-03-15T16:00:00,Room 101,unit,45
   ```

### Manage Events Tab
1. View all events in a table
2. For each event:
   - **Edit**: Opens dialog to refine generated content
   - **Generate**: Triggers n8n to generate content (social post, email, article, ad)

### Edit Event Content
1. Click **"Edit"** button for an event
2. In the dialog:
   - Change **Generation Status**: idle → pending → ready → failed
   - Edit **Generated Content** (JSON format):
     ```json
     {
       "social_post": "Check out our upcoming lecture!",
       "email_newsletter": "Dear Students...",
       "article": "In this week's session...",
       "ad": "Join us for..."
     }
     ```
3. Click **"Save"** to update

## Demo Data

When the seeder runs, you get:

### Demo Convenor Account
- **Email**: `convenor@swin.edu.au`
- **Password**: `password`
- **Role**: Unit Convenor (staff access)

### Demo Students
- **Emails**: `demo_student_1@example.com` through `demo_student_5@example.com`
- **Password**: `password` (for all demo accounts)

### Demo Unit
- **Code**: `DEMO101`
- **Name**: Introduction to Demo
- **5 weekly sessions** (Mondays, 9:00-10:30am)
- **5 enrolled students**

### Demo Notifications
Each demo student has 3 system notifications:
1. Attendance marked for a session
2. Fee payment reminder
3. Event created announcement

## Testing the System

### As Convenor:
1. Login as `convenor@swin.edu.au`
2. Go to **Staff Events**
3. See the event management interface
4. Try uploading a CSV or editing event content

### As Student:
1. Login as `demo_student_1@example.com`
2. Go to **Notifications**
3. See the 3 demo notifications
4. Click "Mark as read" on any notification
5. Switch to **Enrolment** to see your enrollment in DEMO101

## Integration with n8n (Coming Soon)

The system is prepared for n8n integration:

### CSV Import Workflow
- User uploads CSV → `/api/events/import-csv/`
- Webhook forwards to: `https://conditionally-brimful-exie.ngrok-free.dev/webhook-test/import-schedule`
- N8N processes and creates events

### Content Generation Workflow
- Staff clicks "Generate" → Triggers content generation
- N8N can use Claude API to generate social posts, emails, articles, ads
- Results stored in `event.generated_content` JSONField
- Staff reviews and refines content in "Edit" dialog

## Troubleshooting

### No "Staff Events" in Sidebar?
- Make sure you're logged in as a staff user
- Check your `is_staff` flag in the database
- Try logging out and back in

### Notifications Not Showing?
- Make sure you've run the seeder: `docker exec -it cos40005_backend python manage.py seed_student_demo refresh`
- Clear your browser cache (Ctrl+Shift+Delete)
- Check that you're logged in

### CSV Upload Not Working?
- Verify CSV has correct column headers: `title`, `description`, `start`, `end`, `location`, `visibility`, `related_unit_id`
- Check that n8n webhook is running
- Look for error message in the UI

## API Endpoints Reference

### Public API
- `GET /api/core/events/` - List all public events
- `GET /api/core/notifications/` - List current user's notifications (requires auth)

### Staff Only
- `POST /api/core/events/import-csv/` - Upload CSV of events
- `PUT /api/core/events/{id}/refine_content/` - Update event content

### Admin Only
- `GET /api/users/users/` - List all users
- `GET /api/academic/units/` - List all units
