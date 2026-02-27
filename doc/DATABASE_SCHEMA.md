# Database Schema Summary (SwinCMS)

## Overview
- **Database**: SwinCMS (PostgreSQL 18.0)
- **Tables**: 49 total
- **User**: postgres
- **Host**: cos40005_postgres (Docker container)

---

## Table Organization by Module

### Academic Module (6 tables)
1. **academic_course** — Course definitions (code, name, duration, credits)
2. **academic_unit** — Units/modules with convenor reference
3. **academic_semesteroffering** — Offering instances per unit (year, semester, enrollment capacity)
4. **academic_unitresource** — Resources linked to units (files, URLs)
5. **academic_unit_prerequisites** — Prerequisite relationships between units
6. **academic_unit_anti_requisites** — Anti-requisite relationships between units

### Users / Authentication (12 tables)
1. **users_user** — User accounts (email, password, user_type: student/staff/convenor/admin)
2. **users_role** — Role definitions
3. **users_userrole** — M2M: users to roles
4. **users_user_groups** — M2M: users to Django auth groups
5. **users_user_user_permissions** — M2M: users to Django permissions
6. **users_studentprofile** — Extended profile for students (student_id, DOB, gender, enrollment_status)
7. **users_parentguardian** — Parent/guardian records
8. **users_parentguardian_students** — M2M: guardians to students
9. **users_scholarship** — Scholarship definitions
10. **users_scholarshipapplication** — Applications for scholarships
11. **users_auditlog** — Audit trail of user actions
12. **users_n8nworkflow** — n8n workflow configurations (webhook URL, trigger events)
13. **users_n8nexecutionlog** — Execution logs for n8n workflows (status, input/output, errors)

### Enrollment Module (3 tables)
1. **enrollment_enrollment** — Student enrollments in semester offerings (status, grade, marks)
2. **enrollment_enrollmentapproval** — Approval workflow for enrollments
3. **enrollment_transcript** — Academic transcripts (unit code, grade, credits)

### Core Module (13 tables)
1. **core_event** — Events (title, description, start/end times, visibility, **generated_content JSONB, generation_status**)
2. **core_event_attendees** — M2M: events to attendees
3. **core_session** — Teaching sessions (type: lecture/tutorial/lab, date, time, location, instructor)
4. **core_attendancerecord** — Attendance marking (status, notes, marked_by, created_at)
5. **core_notification** — Notifications/alerts (actor, recipient, verb, target)
6. **core_mediaasset** — Uploaded media files (stored as file path in MEDIA_ROOT)
7. **core_form** — Dynamic form definitions (schema as JSONB)
8. **core_formsubmission** — Form responses (data as JSONB)
9. **core_ticket** — Support tickets (title, description, status, priority, category)
10. **core_ticketcomment** — Comments on tickets
11. **core_page** — CMS pages (slug, content, published flag)
12. **core_resource** — Learning resources linked to units
13. **core_session** — Teaching sessions (alternate: see above)

### Social Module (4 tables)
1. **social_achievement** — Achievement/badge definitions
2. **social_studentachievement** — M2M: students to achievements
3. **social_socialgold** — Social points balance per user
4. **social_socialgoldtransaction** — Transactions on social gold points

### Django Built-in (11 tables)
1. **auth_user** — Django's default User (used for framework compatibility)
2. **auth_group** — Django permission groups
3. **auth_permission** — Django app permissions
4. **auth_group_permissions** — M2M: groups to permissions
5. **django_content_type** — Content type registry (app, model)
6. **django_admin_log** — Admin action log
7. **django_session** — Session storage
8. **django_migrations** — Migration history

---

## Key Data Types & Features

### JSONB Columns (Stored as structured JSON)
- **core_event.generated_content** — AI-generated marketing copy (social_post, email_newsletter, long_article, recruitment_ad)
- **core_event.generation_meta** — Metadata about generation (tone, brand_score, bias_flag, prompt_used)
- **core_form.schema** — Dynamic form field definitions
- **core_formsubmission.data** — Submitted form data
- **users_n8nexecutionlog.input_data** — Workflow input payload
- **users_n8nexecutionlog.output_data** — Workflow result
- **users_n8nexecutionlog.error_details** — Error trace if failed

### Timestamps
- Most tables include **created_at** and **updated_at** for audit trails
- Several have **_at** fields: last_generated_at, withdrawn_date, completion_date, etc.

### Constraints
- **Unique constraints** on: user.email, academic_unit.code, academic_course.code, core_form.slug, core_page.slug, users_studentprofile.user_id, etc.
- **Check constraints**: capacity >= 0, current_enrollment >= 0, action_flag >= 0, target_object_id >= 0
- **Not null**: most ID/FK columns, timestamps, core content fields (title, description, etc.)

### Foreign Keys (Relationships)
- **Many-to-one** to users_user: created_by, submitter, assigned_to, uploaded_by, instructor, convenor, actor, recipient, marked_by, etc.
- **Many-to-one** to offerings/units: related_offering_id, related_unit_id, unit_id, etc.
- **Many-to-many** through junction tables: core_event_attendees, users_parentguardian_students, etc.
- **Self-referential FK** in prerequisite/anti-requisite tables (from_unit_id, to_unit_id).

---

## Access & Query Examples

### Connect via CLI
```bash
docker exec -i cos40005_postgres psql -U postgres -d SwinCMS
```

### Common Queries
```sql
-- List all tables
\dt

-- Show schema for core_event
\d public.core_event

-- Count rows per major table
SELECT
  'users_user' as table_name, COUNT(*) as row_count FROM users_user
UNION ALL
SELECT 'core_event', COUNT(*) FROM core_event
UNION ALL
SELECT 'enrollment_enrollment', COUNT(*) FROM enrollment_enrollment
UNION ALL
SELECT 'core_event_attendees', COUNT(*) FROM core_event_attendees
ORDER BY row_count DESC;

-- Events with generated content
SELECT id, title, generation_status, generated_content FROM core_event WHERE generation_status = 'ready';

-- Recent workflow executions
SELECT workflow_id, status, start_time, output_data FROM users_n8nexecutionlog ORDER BY start_time DESC LIMIT 10;

-- Student enrollments
SELECT u.email, e.status, eo.year, eo.semester FROM users_user u 
JOIN enrollment_enrollment e ON u.id = e.student_id 
JOIN academic_semesteroffering eo ON e.offering_id = eo.id;
```

---

## Files in This Repo
- `db_schema_full.sql` — Full schema dump (CREATE TABLE statements)
- `doc/database_erd.puml` — Entity-Relationship Diagram (PlantUML)
- `DATABASE_SCHEMA.md` — This file

---

## Notes
- The system integrates with **n8n** via `N8N_IMPORT_WEBHOOK` and `N8N_WEBHOOK_SECRET` (configured in Django settings).
- **Events** are a central concept: staff uploads CSV → n8n parses & generates content → backend stores in core_event with generated_content JSONB.
- **Media** is stored on the host volume or S3; database stores only file paths.
- **Notifications** use Django's content type framework for flexible targeting.
- **Audit logging** is built in via users_auditlog and django_admin_log.
