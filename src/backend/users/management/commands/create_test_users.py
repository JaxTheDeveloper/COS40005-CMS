from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test users: student, unit convenor, and staff'

    def handle(self, *args, **kwargs):
        # Create a student user
        student_user, created = User.objects.get_or_create(
            email='student@swin.edu.au',
            defaults={
                'username': 'student',
                'first_name': 'Test',
                'last_name': 'Student',
                'is_active': True,
                'user_type': 'student'
            }
        )
        if created:
            student_user.set_password('Test@123')
            student_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created student user: {student_user.email}'))

        # Create a unit convenor user
        convenor_user, created = User.objects.get_or_create(
            email='convenor@swin.edu.au',
            defaults={
                'username': 'convenor',
                'first_name': 'Test',
                'last_name': 'Convenor',
                'is_active': True,
                'user_type': 'unit_convenor'
            }
        )
        if created:
            convenor_user.set_password('Test@123')
            convenor_user.save()
            convenor_user.department = 'Computer Science'
            convenor_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created unit convenor user: {convenor_user.email}'))

        # Create a staff user (admin)
        staff_user, created = User.objects.get_or_create(
            email='staff@swin.edu.au',
            defaults={
                'username': 'staff',
                'first_name': 'Test',
                'last_name': 'Staff',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
                'user_type': 'staff'
            }
        )
        if created:
            staff_user.set_password('Test@123')
            staff_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created staff user: {staff_user.email}'))

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