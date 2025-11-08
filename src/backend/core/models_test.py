from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from src.backend.core.models import Event, Ticket
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

User = get_user_model()

def create_test_event(user, **kwargs):
    """Helper function to create a test event"""
    defaults = {
        'title': 'Test Event',
        'description': 'Test Description',
        'start': timezone.now(),
        'end': timezone.now() + timezone.timedelta(hours=2),
        'created_by': user,
    }
    defaults.update(kwargs)
    return Event.objects.create(**defaults)

class EventModelTests(TestCase):
    def test_create_event(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        event = create_test_event(user)
        self.assertEqual(event.title, 'Test Event')
        self.assertTrue(isinstance(event, Event))

class TicketModelTests(TestCase):
    def test_create_ticket(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Test Description',
            submitter=user
        )
        self.assertEqual(ticket.title, 'Test Ticket')
        self.assertEqual(ticket.submitter, user)