from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test users: student, unit convenor, and staff'

    def handle(self, *args, **kwargs):
        # Create or update a student user
        student_defaults = {
            'username': 'student',
            'first_name': 'Test',
            'last_name': 'Student',
            'is_active': True,
            'user_type': 'student'
        }
        student_user, created = User.objects.update_or_create(
            email='student@swin.edu.au',
            defaults=student_defaults
        )
        if created:
            student_user.set_password('Test@123')
            student_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created student user: {student_user.email}'))
        else:
            # Ensure username exists (fix users created elsewhere without username)
            changed = False
            if not student_user.username:
                student_user.username = student_defaults['username']
                changed = True
            if student_user.user_type != student_defaults['user_type']:
                student_user.user_type = student_defaults['user_type']
                changed = True
            if changed:
                student_user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated student user: {student_user.email}'))

        # Create or update a unit convenor user
        convenor_defaults = {
            'username': 'convenor',
            'first_name': 'Test',
            'last_name': 'Convenor',
            'is_active': True,
            'user_type': 'unit_convenor',
            'department': 'Computer Science'
        }
        convenor_user, created = User.objects.update_or_create(
            email='convenor@swin.edu.au',
            defaults=convenor_defaults
        )
        if created:
            convenor_user.set_password('Test@123')
            convenor_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created unit convenor user: {convenor_user.email}'))
        else:
            changed = False
            if not convenor_user.username:
                convenor_user.username = convenor_defaults['username']
                changed = True
            if convenor_user.user_type != convenor_defaults['user_type']:
                convenor_user.user_type = convenor_defaults['user_type']
                changed = True
            if convenor_user.department != convenor_defaults['department']:
                convenor_user.department = convenor_defaults['department']
                changed = True
            if changed:
                convenor_user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated unit convenor user: {convenor_user.email}'))

        # Create or update a staff user (admin)
        staff_defaults = {
            'username': 'staff',
            'first_name': 'Test',
            'last_name': 'Staff',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
            'user_type': 'staff'
        }
        staff_user, created = User.objects.update_or_create(
            email='staff@swin.edu.au',
            defaults=staff_defaults
        )
        if created:
            staff_user.set_password('Test@123')
            staff_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created staff user: {staff_user.email}'))
        else:
            changed = False
            # Ensure staff flags and username are set correctly
            if not staff_user.username:
                staff_user.username = staff_defaults['username']
                changed = True
            if staff_user.user_type != staff_defaults['user_type']:
                staff_user.user_type = staff_defaults['user_type']
                changed = True
            if not staff_user.is_staff or not staff_user.is_superuser:
                staff_user.is_staff = True
                staff_user.is_superuser = True
                changed = True
            if changed:
                staff_user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated staff user: {staff_user.email}'))

        self.stdout.write(self.style.SUCCESS('Test users created successfully!'))
        self.stdout.write('\nLogin credentials for all users:')
        self.stdout.write('----------------------------------------')
        self.stdout.write('Student:')
        self.stdout.write('Email: student@swin.edu.au')
        self.stdout.write('Password: Test@123')
        self.stdout.write('\nUnit Convenor:')
        self.stdout.write('Email: convenor@swin.edu.au')
        self.stdout.write('Password: Test@123')
        self.stdout.write('\nStaff/Admin:')
        self.stdout.write('Email: staff@swin.edu.au')
        self.stdout.write('Password: Test@123')
        self.stdout.write('----------------------------------------')