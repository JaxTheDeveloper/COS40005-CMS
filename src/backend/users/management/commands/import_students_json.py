from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ...models import StudentProfile
import json
import os
from datetime import date

User = get_user_model()

class Command(BaseCommand):
    help = 'Import students from students.json into PostgreSQL'

    def handle(self, *args, **kwargs):
        # In Docker, /app is the project root
        json_path = '/app/data/students.json'
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'File not found: {json_path}'))
            return
        with open(json_path, 'r', encoding='utf-8') as f:
            students = json.load(f)
        for entry in students:
            user_defaults = {
                'username': entry['username'],
                'first_name': entry['full_name'].split()[0],
                'last_name': ' '.join(entry['full_name'].split()[1:]),
                'is_active': True,
                'user_type': 'student',
            }
            user, created = User.objects.get_or_create(
                email=entry['email'],
                defaults=user_defaults
            )
            if created:
                user.set_password(entry['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {user.email}'))
            else:
                self.stdout.write(f'User already exists: {user.email}')
            # Create or update StudentProfile
            profile_defaults = {
                'enrollment_date': date.today(),
                'course': None,
            }
            StudentProfile.objects.get_or_create(
                user=user,
                defaults=profile_defaults
            )
        self.stdout.write(self.style.SUCCESS('Student import complete.'))
