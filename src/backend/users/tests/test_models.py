from django.test import TestCase
from django.utils import timezone
from ..models import User, StudentProfile, Course, Unit, Enrollment


class StudentProfileSignalTests(TestCase):
    def test_studentprofile_created_on_user_creation(self):
        u = User.objects.create(email='student1@example.com', username='student1', user_type='student')
        # refresh from db
        self.assertTrue(StudentProfile.objects.filter(user=u).exists())
        sp = StudentProfile.objects.get(user=u)
        self.assertTrue(sp.student_id.startswith('S-'))


class EnrollmentTests(TestCase):
    def setUp(self):
        self.student = User.objects.create(email='s2@example.com', username='s2', user_type='student')
        self.course = Course.objects.create(code='C101', name='Course 101')
        # ensure student profile exists
        StudentProfile.objects.filter(user=self.student).update(course=self.course)
        self.unit = Unit.objects.create(code='U101', name='Unit 101')

    def test_enrollment_unique_constraint(self):
        e1 = Enrollment.objects.create(student=self.student, unit=self.unit, semester='S1', year=2025, status='enrolled')
        # Creating duplicate enrollment should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(student=self.student, unit=self.unit, semester='S1', year=2025, status='enrolled')
