from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from src.backend.core.models import Event, Ticket, Form
from src.backend.academic.models import Unit, SemesterOffering
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

User = get_user_model()

class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teststaff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=2),
            created_by=self.user
        )

    def test_event_creation(self):
        self.assertEqual(self.event.title, 'Test Event')
        self.assertEqual(self.event.description, 'Test Description')
        self.assertTrue(isinstance(self.event, Event))
        self.assertEqual(str(self.event), 'Test Event')

class TicketModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teststudent',
            email='student@test.com',
            password='testpass123',
            user_type='student'
        )
        self.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Help needed',
            submitter=self.user
        )

    def test_ticket_creation(self):
        self.assertEqual(self.ticket.title, 'Test Ticket')
        self.assertEqual(self.ticket.description, 'Help needed')
        self.assertEqual(self.ticket.submitter, self.user)
        self.assertTrue(isinstance(self.ticket, Ticket))

class CoreAPITest(APITestCase):
    def setUp(self):
        # Create a staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        # Create a student user
        self.student_user = User.objects.create_user(
            username='studentuser',
            email='student@test.com',
            password='testpass123',
            user_type='student'
        )
        # Create test event
        self.event = Event.objects.create(
            title='API Test Event',
            description='API Test Description',
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=2),
            created_by=self.staff_user
        )
        # Create test ticket
        self.ticket = Ticket.objects.create(
            title='API Test Ticket',
            description='API Help needed',
            submitter=self.student_user
        )

    def test_list_events(self):
        """Test that events can be listed"""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'API Test Event')

    def test_create_ticket(self):
        """Test that students can create tickets"""
        self.client.force_authenticate(user=self.student_user)
        url = reverse('ticket-list')
        data = {
            'title': 'New Test Ticket',
            'description': 'Need help with assignment'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Test Ticket')
        self.assertEqual(response.data['submitter'], self.student_user.id)