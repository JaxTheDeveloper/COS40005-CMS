from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time

from src.backend.users.models import User
from src.backend.academic.models import Course, Unit, SemesterOffering
from src.backend.enrollment.models import Enrollment
from src.backend.core.models import Session, AttendanceRecord, Notification
import random
import json
import os


class Command(BaseCommand):
    help = 'Seed demo students, units, offerings and sessions with a convenor/instructor. Use "refresh" to wipe existing demo data.'

    def add_arguments(self, parser):
        parser.add_argument('action', nargs='?', choices=['refresh', 'seed'], default='seed')

    def handle(self, *args, **options):
        action = options.get('action')

        if action == 'refresh':
            self.stdout.write('Refreshing demo data...')
            self._clear_demo()

        self._seed()
        self.stdout.write(self.style.SUCCESS('Demo seed complete.'))

    def _clear_demo(self):
        # Remove demo objects recorded in data/demo_seed.json if present
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '..', '..', '..', '..', 'data', 'demo_seed.json')
        # The above constructs project-root/data/demo_seed.json relatively; fall back to project data folder
        # Simpler: look for repository-root/data/demo_seed.json
        repo_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'data', 'demo_seed.json'))
        candidates = [repo_data_path]
        seed_path = None
        for p in candidates:
            if os.path.exists(p):
                seed_path = p
                break

        if seed_path:
            try:
                with open(seed_path, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                # Delete in reverse-safe order
                # Notifications
                for nid in payload.get('notifications', []):
                    try:
                        Notification.objects.filter(pk=nid).delete()
                    except Exception:
                        pass
                # Attendance
                for aid in payload.get('attendance', []):
                    try:
                        AttendanceRecord.objects.filter(pk=aid).delete()
                    except Exception:
                        pass
                # Enrollments
                for eid in payload.get('enrollments', []):
                    try:
                        Enrollment.objects.filter(pk=eid).delete()
                    except Exception:
                        pass
                # Sessions
                for sid in payload.get('sessions', []):
                    try:
                        Session.objects.filter(pk=sid).delete()
                    except Exception:
                        pass
                # Offerings
                for oid in payload.get('offerings', []):
                    try:
                        SemesterOffering.objects.filter(pk=oid).delete()
                    except Exception:
                        pass
                # Units
                for uid in payload.get('units', []):
                    try:
                        Unit.objects.filter(pk=uid).delete()
                    except Exception:
                        pass
                # Users
                for usid in payload.get('users', []):
                    try:
                        User.objects.filter(pk=usid).delete()
                    except Exception:
                        pass
                # Remove seed file
                try:
                    os.remove(seed_path)
                except Exception:
                    pass
                self.stdout.write(self.style.NOTICE(f'Removed demo objects listed in {seed_path}'))
                return
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Failed to read demo seed file: {e}'))

        # Fallback aggressive removal for legacy demo markers
        User.objects.filter(email__icontains='demo_').delete()
        Unit.objects.filter(code__icontains='DEMO').delete()

    def _seed(self):
        now = timezone.now()

        # Ensure unit convenor exists (academic department)
        convenor_email = 'convenor@swin.edu.au'
        convenor, created = User.objects.get_or_create(
            email=convenor_email,
            defaults={
                'username': 'convenor',
                'is_staff': True,  # Django staff flag for admin access
                'first_name': 'Unit',
                'last_name': 'Convenor',
                'user_type': 'unit_convenor',  # Academic department role
            }
        )
        if created:
            convenor.set_password('password')
            convenor.save()
        
        # Also create a HQ staff account for testing
        staff_email = 'staff@swin.edu.au'
        staff_user, staff_created = User.objects.get_or_create(
            email=staff_email,
            defaults={
                'username': 'hq_staff',
                'is_staff': True,
                'first_name': 'HQ',
                'last_name': 'Staff',
                'user_type': 'staff',  # HQ staff role
            }
        )
        if staff_created:
            staff_user.set_password('password')
            staff_user.save()

        # Create a demo course and unit
        course, _ = Course.objects.get_or_create(code='DEMO-COS', defaults={'name': 'Demo Course'})

        unit, _ = Unit.objects.get_or_create(
            code='DEMO101',
            defaults={
                'name': 'Introduction to Demo',
                'convenor': convenor,
            }
        )

        # Make sure unit convenor is set
        if unit.convenor_id != convenor.id:
            unit.convenor = convenor
            unit.save()

        # Create an offering for current semester
        year = now.year
        semester = 'S1'
        offering, _ = SemesterOffering.objects.get_or_create(
            unit=unit,
            year=year,
            semester=semester,
            defaults={
                'enrollment_start': now - timezone.timedelta(days=7),
                'enrollment_end': now + timezone.timedelta(days=90),
                'capacity': 100,
                'current_enrollment': 0,
            }
        )

        # Create some demo sessions and assign convenor as instructor
        for week in range(1, 6):
            date = (now + timedelta(days=7 * week)).date()
            Session.objects.get_or_create(
                offering=offering,
                unit=offering.unit,
                date=date,
                defaults={
                    'session_type': 'lecture',
                    'start_time': datetime.strptime('09:00', '%H:%M').time(),
                    'end_time': datetime.strptime('10:30', '%H:%M').time(),
                    'location': 'Room 101',
                    'instructor': convenor,
                }
            )

        created_ids = {
            'users': [],
            'units': [],
            'offerings': [],
            'sessions': [],
            'enrollments': [],
            'attendance': [],
            'notifications': [],
        }

        # Create a few demo students and enroll them
        for i in range(1, 6):
            email = f'demo_student_{i}@example.com'
            student, created = User.objects.get_or_create(
                email=email,
                defaults={'username': f'demo_student_{i}', 'is_staff': False}
            )
            if created:
                student.set_password('password')
                student.save()
            created_ids['users'].append(student.pk)
            # Enroll student if not already
            enrollment, enr_created = Enrollment.objects.get_or_create(student=student, offering=offering, defaults={'status': 'ENROLLED'})
            created_ids['enrollments'].append(enrollment.pk)

        # Update offering current_enrollment
        offering.current_enrollment = Enrollment.objects.filter(offering=offering, status='ENROLLED').count()
        offering.save()

        # Seed attendance records for sessions and enrolled students
        sessions = list(Session.objects.filter(offering=offering))
        for s in sessions:
            created_ids['sessions'].append(s.pk)

        enrolled_students = [e.student for e in Enrollment.objects.filter(offering=offering, status='ENROLLED')]
        status_choices = ['present', 'late', 'absent', 'excused']
        weights = [0.8, 0.1, 0.08, 0.02]

        for session in sessions:
            for student in enrolled_students:
                status = random.choices(status_choices, weights)[0]
                attendance, a_created = AttendanceRecord.objects.get_or_create(
                    session=session,
                    student=student,
                    defaults={'status': status, 'marked_by': convenor}
                )
                created_ids['attendance'].append(attendance.pk)

        # Record created offering/unit/user IDs for future refresh deletion
        created_ids['offerings'].append(offering.pk)
        created_ids['units'].append(unit.pk)
        # course not recorded as it may be shared; record convenor and staff
        created_ids['users'].append(convenor.pk)
        created_ids['users'].append(staff_user.pk)

        # Seed demo notifications for students
        for student in enrolled_students:
            # Attendance notification (marked for latest session)
            if sessions:
                latest_session = sessions[-1]
                attendance_notif, _ = Notification.objects.get_or_create(
                    recipient=student,
                    verb='attendance_marked',
                    target_content_type_id=None,
                    target_object_id=None,
                    defaults={'actor': convenor, 'unread': True}
                )
                created_ids['notifications'].append(attendance_notif.pk)

            # Fee payment reminder notification
            fee_notif, _ = Notification.objects.get_or_create(
                recipient=student,
                verb='fees_due',
                target_content_type_id=None,
                target_object_id=None,
                defaults={
                    'actor': convenor,
                    'unread': True,
                }
            )
            created_ids['notifications'].append(fee_notif.pk)

            # Event notification (unit event)
            event_notif, _ = Notification.objects.get_or_create(
                recipient=student,
                verb='event_created',
                target_content_type_id=None,
                target_object_id=None,
                defaults={'actor': convenor, 'unread': True}
            )
            created_ids['notifications'].append(event_notif.pk)

        # Write seed record to data/demo_seed.json in repo root
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
        data_dir = os.path.join(repo_root, 'data')
        os.makedirs(data_dir, exist_ok=True)
        seed_path = os.path.join(data_dir, 'demo_seed.json')
        try:
            with open(seed_path, 'w', encoding='utf-8') as f:
                json.dump(created_ids, f, indent=2)
            self.stdout.write(self.style.SUCCESS(f'Wrote demo seed record to {seed_path}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to write demo seed file: {e}'))

        # Print summary
        self.stdout.write('Created demo objects:')
        self.stdout.write(f" Users: {created_ids['users']}")
        self.stdout.write(f" Units: {created_ids['units']}")
        self.stdout.write(f" Offerings: {created_ids['offerings']}")
        self.stdout.write(f" Sessions: {created_ids['sessions']}")
        self.stdout.write(f" Enrollments: {created_ids['enrollments']}")
        self.stdout.write(f" Attendance: {created_ids['attendance']}")
        self.stdout.write(f" Notifications: {created_ids['notifications']}")
