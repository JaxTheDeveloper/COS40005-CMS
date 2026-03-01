import os
import django
import unittest

# ensure settings loaded when importing server
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.backend.settings")
django.setup()

from fastapi.testclient import TestClient
from tools.mcp_server import app, SERVICE_TOKEN
from django.contrib.auth import get_user_model
from src.backend.academic.models import Course, Unit, CourseUnit
from src.backend.enrollment.models import Enrollment
from src.backend.academic.models import SemesterOffering

User = get_user_model()

class MCPServerTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.student = User.objects.create_user(email='a@b.com', username='a', password='p', user_type='student')
        unit = Unit.objects.create(code='X101', name='Test unit')
        offering = SemesterOffering.objects.create(unit=unit, year=2025, semester='S1', enrollment_start=django.utils.timezone.now(), enrollment_end=django.utils.timezone.now())
        Enrollment.objects.create(student=self.student, offering=offering)
        course = Course.objects.create(code='C100', name='Course')
        CourseUnit.objects.create(course=course, unit=unit)

    def auth_headers(self):
        if SERVICE_TOKEN:
            return {'Authorization': f'Token {SERVICE_TOKEN}'}
        return {}

    def test_tools_list(self):
        r = self.client.get('/tools', headers=self.auth_headers())
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.json(), list)

    def test_get_student_profile(self):
        r = self.client.get('/get_student_profile', params={'email': self.student.email}, headers=self.auth_headers())
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['user']['email'], self.student.email)
        self.assertTrue(len(data['enrollments']) >= 1)

    def test_list_units(self):
        r = self.client.get('/list_available_units', params={'course_code': 'C100'}, headers=self.auth_headers())
        self.assertEqual(r.status_code, 200)
        self.assertTrue('units' in r.json())

if __name__ == '__main__':
    unittest.main()
