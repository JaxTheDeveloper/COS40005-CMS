from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from src.backend.core.models import Event, Ticket

User = get_user_model()

class CoreAPIPermissionTests(APITestCase):
    def setUp(self):
        # Users
        self.staff = User.objects.create_user(
            username='staff_api', email='staff_api@test.com', password='pw', is_staff=True
        )
        self.convenor = User.objects.create_user(
            username='conv_api', email='conv_api@test.com', password='pw', user_type='unit_convenor'
        )
        self.student = User.objects.create_user(
            username='stud_api', email='stud_api@test.com', password='pw', user_type='student'
        )

        # Create an event by staff directly
        self.event = Event.objects.create(
            title='Existing Event',
            description='Existing',
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1),
            created_by=self.staff
        )

        # Ticket created by student
        self.ticket = Ticket.objects.create(
            title='Student Ticket', description='Help', submitter=self.student
        )

    def test_event_list_authenticated(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('event-list')
        resp = self.client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        titles = [r['title'] for r in resp.data]
        assert 'Existing Event' in titles

    def test_event_create_by_convenor_allowed(self):
        self.client.force_authenticate(user=self.convenor)
        url = reverse('event-list')
        data = {
            'title': 'Conv Created',
            'description': 'By conv',
            'start': timezone.now().isoformat(),
            'end': (timezone.now() + timezone.timedelta(hours=2)).isoformat(),
        }
        resp = self.client.post(url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['title'] == 'Conv Created'

    def test_event_create_by_student_forbidden(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('event-list')
        data = {
            'title': 'Student Created',
            'description': 'By student',
            'start': timezone.now().isoformat(),
            'end': (timezone.now() + timezone.timedelta(hours=2)).isoformat(),
        }
        resp = self.client.post(url, data)
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST)

    def test_ticket_create_by_student(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('ticket-list')
        data = {'title': 'API Ticket', 'description': 'Need help'}
        resp = self.client.post(url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['title'] == 'API Ticket'
        # HiddenField (submitter) does not appear in response by default; verify DB state
        from src.backend.core.models import Ticket as TicketModel
        t = TicketModel.objects.get(title='API Ticket')
        assert t.submitter == self.student

    def test_ticket_update_permissions(self):
        # other student cannot edit
        other = User.objects.create_user(username='other', email='o@test.com', password='pw', user_type='student')
        self.client.force_authenticate(user=other)
        url = reverse('ticket-detail', args=[self.ticket.id])
        resp = self.client.patch(url, {'description': 'Hacked'})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # owner can edit
        self.client.force_authenticate(user=self.student)
        resp = self.client.patch(url, {'description': 'Updated by owner'})
        assert resp.status_code == status.HTTP_200_OK

        # staff can edit
        self.client.force_authenticate(user=self.staff)
        resp = self.client.patch(url, {'description': 'Updated by staff'})
        assert resp.status_code == status.HTTP_200_OK
