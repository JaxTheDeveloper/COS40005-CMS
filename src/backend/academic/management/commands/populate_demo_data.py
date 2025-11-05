from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from src.backend.academic.models import Unit, SemesterOffering
from src.backend.users.models import User, StudentProfile, Course


class Command(BaseCommand):
    help = 'Populate demo units and demo student users (Australian, Russian, Vietnamese)'

    def handle(self, *args, **options):
        self.stdout.write('Populating demo units...')

        # Create or get a demo course
        course, _ = Course.objects.get_or_create(code='COS-BSC', defaults={
            'name': 'Bachelor of Computer Science',
            'description': 'Demo course',
            'credit_points': 240,
        })

        # Unit definitions
        units_def = [
            ('COS10009', 'Introduction to Programming', 'An introduction to programming concepts and Python.'),
            ('COS10004', 'Computer Systems', 'Basics of computer hardware and OS.'),
            ('TNE10006', 'Networks and Switching', 'Networking fundamentals and switching.'),
            ('COS10026', 'Computing Inquiry Project', 'Project-based learning, small computing project.'),
            ('COS20017', 'Object-Oriented Programming', 'OOP principles and design patterns.'),
        ]

        created_units = {}
        for code, name, desc in units_def:
            unit, created = Unit.objects.get_or_create(code=code, defaults={
                'name': name,
                'description': desc,
                'credit_points': 6,
            })
            created_units[code] = unit
            if created:
                self.stdout.write(f'  Created unit {code}')
            else:
                self.stdout.write(f'  Unit {code} already exists')

        # Set up prerequisites
        self.stdout.write('Setting prerequisites...')
        # TNE10006 prerequisites: COS10009
        tne = created_units.get('TNE10006')
        cos10009 = created_units.get('COS10009')
        if tne and cos10009:
            tne.prerequisites.set([cos10009])
            tne.save()

        # COS10026 prerequisites: COS10004 and COS10009
        cos10026 = created_units.get('COS10026')
        cos10004 = created_units.get('COS10004')
        if cos10026 and cos10004 and cos10009:
            cos10026.prerequisites.set([cos10004, cos10009])
            cos10026.save()

        # COS20017 prerequisites: COS10026 and COS10009
        cos20017 = created_units.get('COS20017')
        if cos20017 and cos10026 and cos10009:
            cos20017.prerequisites.set([cos10026, cos10009])
            cos20017.save()

        # Create SemesterOfferings for current year, S1
        self.stdout.write('Creating semester offerings...')
        now = timezone.now()
        enroll_start = now - timedelta(days=30)
        enroll_end = now + timedelta(days=180)
        year = now.year
        for unit in created_units.values():
            so, created = SemesterOffering.objects.get_or_create(
                unit=unit,
                year=year,
                semester='S1',
                defaults={
                    'enrollment_start': enroll_start,
                    'enrollment_end': enroll_end,
                    'capacity': 200,
                }
            )
            if created:
                self.stdout.write(f'  Offering created for {unit.code} {year} S1')

        # Create demo students
        self.stdout.write('Creating demo student users...')

        demo_students = [
            # Australian
            ('oliver.smith@demo.edu', 'Oliver Smith', 'Australia'),
            ('amelia.jones@demo.edu', 'Amelia Jones', 'Australia'),
            # Russian
            ('ivan.petrov@demo.edu', 'Ivan Petrov', 'Russia'),
            ('olga.ivanova@demo.edu', 'Olga Ivanova', 'Russia'),
            # Vietnamese
            ('nguyen.van.a@demo.edu', 'Nguyen Van A', 'Vietnam'),
            ('pham.thi.b@demo.edu', 'Pham Thi B', 'Vietnam'),
        ]

        for email, full_name, country in demo_students:
            username = email.split('@')[0]
            if User.objects.filter(email=email).exists():
                self.stdout.write(f'  User {email} already exists')
                continue
            first, *last = full_name.split(' ')
            last_name = ' '.join(last) if last else ''
            user = User.objects.create_user(email=email, username=username, password='password123')
            user.first_name = first
            user.last_name = last_name
            user.country = country
            user.user_type = 'student'
            user.save()

            # Create or get StudentProfile
            sp, sp_created = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'student_id': f'S-{user.id:06d}',
                    'enrollment_date': now.date(),
                    'course': course,
                }
            )
            if sp_created:
                self.stdout.write(f'  Created student {full_name} <{email}>')
            else:
                self.stdout.write(f'  StudentProfile for {email} already exists')

        self.stdout.write(self.style.SUCCESS('Demo data population complete.'))
