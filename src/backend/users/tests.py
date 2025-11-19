from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class TestStudentListAPI(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email='teststudent@swin.edu.au',
            username='teststudent',
            password='password123',
            user_type='student',
            first_name='Test',
            last_name='Student'
        )
        self.url = reverse('student-list')

    def test_student_list_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_student_list_returns_students(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        emails = [s['email'] for s in response.data]
        self.assertIn('teststudent@swin.edu.au', emails)
