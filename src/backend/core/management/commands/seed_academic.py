from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import json
import os


class Command(BaseCommand):
    help = 'Seed academic data: units, offerings, students, and enrollments from JSON files in data/'

    def add_arguments(self, parser):
        parser.add_argument('--data-dir', type=str, default=os.path.join(settings.BASE_DIR, 'data'), help='Directory containing units.json and students.json')
        parser.add_argument('--enroll-student', type=str, help='Username of an existing user to enroll into all created offerings')

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        units_file = os.path.join(data_dir, 'units.json')
        students_file = os.path.join(data_dir, 'students.json')

        from src.backend.academic.models import Unit, SemesterOffering
        from src.backend.enrollment.models import Enrollment
        from django.contrib.auth import get_user_model

        User = get_user_model()

        if not os.path.exists(units_file):
            self.stdout.write(self.style.ERROR(f"Units file not found: {units_file}"))
            return

        with open(units_file, 'r', encoding='utf-8') as fh:
            units_data = json.load(fh)

        # optional: read a CSV that lists core unit codes (one code per line)
        core_codes = set()
        core_csv = os.path.join(data_dir, 'core_units.csv')
        if os.path.exists(core_csv):
            try:
                import csv
                with open(core_csv, 'r', encoding='utf-8') as cf:
                    reader = csv.reader(cf)
                    for row in reader:
                        if not row:
                            continue
                        code = row[0].strip()
                        if code:
                            core_codes.add(code)
                self.stdout.write(self.style.SUCCESS(f"Loaded {len(core_codes)} core unit codes from {core_csv}"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed to read core_units.csv: {e}"))

        # helper to guess a unit major from unit code prefix
        def guess_major(code):
            if not code:
                return 'General'
            if code.startswith('COS'):
                return 'Computer Science'
            if code.startswith(('BUS','FIN','MKT','ACC','INB','MGT')):
                return 'Business'
            if code.startswith(('MDA','DCO','COM','PUB')):
                return 'Media & Communications'
            return 'General'

        # Create units (first pass) and persist unit.department when available
        created_units = {}
        for u in units_data:
            code = u.get('code')
            name = u.get('name')
            descr = u.get('description', '')
            cp = u.get('credit_points', 10)
            unit_major = u.get('major') or guess_major(code)
            defaults = {'name': name, 'description': descr, 'credit_points': cp, 'department': unit_major}
            unit, created = Unit.objects.update_or_create(code=code, defaults=defaults)
            created_units[code] = unit
            self.stdout.write(self.style.SUCCESS(f"Unit {'created' if created else 'updated'}: {code}"))

        # Second pass: set prerequisites and anti_requisites
        for u in units_data:
            code = u.get('code')
            unit = created_units.get(code)
            prereq_codes = u.get('prerequisites', [])
            anti_codes = u.get('anti_requisites', [])
            if prereq_codes:
                prereqs = [created_units[c] for c in prereq_codes if c in created_units]
                unit.prerequisites.set(prereqs)
            if anti_codes:
                antis = [created_units[c] for c in anti_codes if c in created_units]
                unit.anti_requisites.set(antis)
            unit.save()

        # Create offerings
        for u in units_data:
            code = u.get('code')
            unit = created_units.get(code)
            offerings = u.get('offerings', [])
            for off in offerings:
                year = off.get('year', timezone.now().year)
                semester = off.get('semester', 'S1')
                enrollment_start = off.get('enrollment_start')
                enrollment_end = off.get('enrollment_end')
                capacity = off.get('capacity', 0)
                # parse datetimes if strings
                from django.utils.dateparse import parse_datetime
                if isinstance(enrollment_start, str):
                    enrollment_start = parse_datetime(enrollment_start)
                if isinstance(enrollment_end, str):
                    enrollment_end = parse_datetime(enrollment_end)
                if enrollment_start is None:
                    enrollment_start = timezone.now()
                if enrollment_end is None:
                    enrollment_end = timezone.now() + timezone.timedelta(days=30)

                # determine unit-level major/category (either provided in JSON or guessed from code prefix)
                def guess_major(code):
                    if code.startswith('COS'):
                        return 'Computer Science'
                    if code.startswith('BUS') or code.startswith('FIN') or code.startswith('MKT') or code.startswith('ACC') or code.startswith('INB') or code.startswith('MGT'):
                        return 'Business'
                    if code.startswith('MDA') or code.startswith('DCO') or code.startswith('COM') or code.startswith('PUB'):
                        return 'Media & Communications'
                    return 'General'

                unit_major = u.get('major') or guess_major(code)
                # category can be provided in JSON, or derived from core_units.csv
                category = u.get('category')  # optional: 'core'|'major'|'elective'
                if not category and code in core_codes:
                    category = 'core'

                # collect optional scheduling metadata and place into offering notes
                class_hours = off.get('class_hours')
                meeting_day = off.get('meeting_day')
                meeting_time = off.get('meeting_time')
                notes_parts = []
                # include unit major and category so frontend can group offerings
                if unit_major:
                    notes_parts.append(f"Major: {unit_major}")
                if category:
                    notes_parts.append(f"Category: {category}")
                if class_hours:
                    notes_parts.append(f"Class {class_hours}h/week")
                if meeting_day and meeting_time:
                    notes_parts.append(f"{meeting_day} {meeting_time}")
                notes = '; '.join(notes_parts)

                defaults = {
                    'enrollment_start': enrollment_start,
                    'enrollment_end': enrollment_end,
                    'capacity': capacity,
                }
                if notes:
                    defaults['notes'] = notes

                so, created = SemesterOffering.objects.update_or_create(unit=unit, year=year, semester=semester, defaults=defaults)
                self.stdout.write(self.style.SUCCESS(f"Offering {'created' if created else 'updated'}: {so}"))

    # Create students and optionally enroll
        if os.path.exists(students_file):
            with open(students_file, 'r', encoding='utf-8') as fh:
                students_data = json.load(fh)

            for s in students_data:
                username = s.get('username')
                email = s.get('email')
                password = s.get('password', 'password123')
                user, created = User.objects.update_or_create(username=username, defaults={'email': email, 'is_active': True})
                user.set_password(password)
                # store student's major into user.department so frontend can read it
                student_major = s.get('major')
                if student_major:
                    user.department = student_major
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Student {'created' if created else 'updated'}: {username} ({email})"))

                # enrollments: list of {unit_code, year, semester}
                enrolls = s.get('enrollments', [])
                for e in enrolls:
                    ucode = e.get('unit_code')
                    year = e.get('year', timezone.now().year)
                    semester = e.get('semester', 'S1')
                    unit = created_units.get(ucode)
                    if not unit:
                        self.stdout.write(self.style.WARNING(f"Unit for enrollment not found: {ucode}"))
                        continue
                    try:
                        offering = SemesterOffering.objects.get(unit=unit, year=year, semester=semester)
                    except SemesterOffering.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Offering not found for {ucode} {semester} {year}, creating default offering."))
                        offering = SemesterOffering.objects.create(unit=unit, year=year, semester=semester, enrollment_start=timezone.now(), enrollment_end=timezone.now()+timezone.timedelta(days=30), capacity=100)

                    # Create enrollment
                    enrollment, created_en = Enrollment.objects.update_or_create(student=user, offering=offering, defaults={'status': 'ENROLLED'})
                    if created_en:
                        # increment offering current enrollment
                        offering.current_enrollment = offering.current_enrollment + 1
                        offering.save()
                    self.stdout.write(self.style.SUCCESS(f"Enrollment {'created' if created_en else 'updated'}: {user.username} -> {offering}"))

        else:
            self.stdout.write(self.style.WARNING(f"Students file not found: {students_file} — skipping students creation"))

        # If --enroll-student provided, enroll that user into all offerings
        enroll_user = options.get('enroll_student')
        if enroll_user:
            try:
                user = User.objects.get(username=enroll_user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User not found: {enroll_user}"))
            else:
                from src.backend.academic.models import SemesterOffering
                offerings = SemesterOffering.objects.filter(is_active=True)
                for offering in offerings:
                    enrollment, created_en = Enrollment.objects.get_or_create(student=user, offering=offering, defaults={'status': 'ENROLLED'})
                    if created_en:
                        offering.current_enrollment = offering.current_enrollment + 1
                        offering.save()
                    self.stdout.write(self.style.SUCCESS(f"Enrolled {user.username} -> {offering}"))

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
