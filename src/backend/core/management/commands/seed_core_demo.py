from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from src.backend.core import models as core_models
from src.backend.academic.models import Unit, SemesterOffering

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for core app (events, sessions, tickets, forms)'

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # Pick an existing unit if available
        unit = Unit.objects.first()
        offering = SemesterOffering.objects.first()

        # Pick users
        student = User.objects.filter(user_type='student').first()
        convenor = User.objects.filter(user_type='unit_convenor').first()
        staff = User.objects.filter(is_staff=True).first()

        # Create an event
        event, _ = core_models.Event.objects.update_or_create(
            title='Demo Orientation',
            defaults={
                'description': 'Welcome event for demo users',
                'start': now + timezone.timedelta(days=1),
                'end': now + timezone.timedelta(days=1, hours=2),
                'created_by': staff or convenor,
                'related_unit': unit,
                'related_offering': offering,
            }
        )
        if student:
            event.attendees.add(student)

        # Create a session
        if unit and offering and convenor:
            session = core_models.Session.objects.create(
                unit=unit,
                offering=offering,
                session_type='lecture',
                date=timezone.localdate() + timezone.timedelta(days=2),
                start_time=timezone.datetime.now().time(),
                instructor=convenor,
            )

        # Create a ticket
        if student:
            ticket = core_models.Ticket.objects.create(
                title='Demo ticket',
                description='I need help with enrollment',
                submitter=student,
                related_unit=unit,
            )

        # Create a form
        form, _ = core_models.Form.objects.update_or_create(
            slug='course-feedback',
            defaults={
                'name': 'Course Feedback',
                'schema': {'fields': [{'name': 'rating', 'type': 'integer'}, {'name': 'comments', 'type': 'string'}]},
                'created_by': convenor or staff,
            }
        )

        self.stdout.write(self.style.SUCCESS('Core demo data seeded.'))
