from django.test import TestCase
from django.contrib.auth import get_user_model
from src.backend.academic.models import Unit, SemesterOffering
from src.backend.enrollment.models import Enrollment, EnrollmentApproval
from src.backend.core.models import Notification
from django.utils import timezone

User = get_user_model()


def make_offering():
    unit = Unit.objects.create(code='TST101', name='Test Unit', credit_points=6)
    return SemesterOffering.objects.create(
        unit=unit,
        year=2025,
        semester='S1',
        enrollment_start=timezone.now() - timezone.timedelta(days=1),
        enrollment_end=timezone.now() + timezone.timedelta(days=30),
    )


class EnrollmentNotificationTests(TestCase):
    def setUp(self):
        # create a student and a staff user to act as convenor
        self.student = User.objects.create_user(
            email='student@example.com',
            username='stud',
            password='pwd',
            user_type='student',
        )
        self.staff = User.objects.create_user(
            email='staff@example.com',
            username='staff',
            password='pwd',
            is_staff=True,
            user_type='staff',
        )
        # assign the unit convenor to the staff user
        offering = make_offering()
        offering.unit.convenor = self.staff
        offering.unit.save()
        self.offering = offering
        self.enrollment = Enrollment.objects.create(student=self.student, offering=self.offering)

    def test_notification_on_approve(self):
        # creation produced a pending notification; wipe them before continuing
        Notification.objects.all().delete()
        self.assertEqual(Notification.objects.count(), 0)

        approval = EnrollmentApproval.objects.create(enrollment=self.enrollment)
        approval.approve(approver=self.student)

        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, 'ENROLLED')
        # only the student notification should exist now
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.recipient, self.student)
        self.assertIn('enrolled', notif.verb.lower())
        self.assertEqual(notif.target_object_id, self.enrollment.pk)

    def test_notify_staff_on_new_pending(self):
        # the initial creation (setUp) should have produced a pending notification
        staff_notifs = Notification.objects.filter(recipient=self.staff)
        self.assertTrue(staff_notifs.exists())
        self.assertIn('pending approval', staff_notifs.first().verb.lower())

        # also all staff users should receive it
        all_staff_notifs = Notification.objects.filter(recipient__is_staff=True)
        self.assertTrue(all_staff_notifs.exists())

    def test_notification_on_withdraw(self):
        # approve first so that offering count is incremented properly
        approval = EnrollmentApproval.objects.create(enrollment=self.enrollment)
        approval.approve(approver=self.student)

        # clear any prior notifications and then withdraw
        Notification.objects.all().delete()
        self.enrollment.withdraw()

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.recipient, self.student)
        self.assertIn('withdrawn', notif.verb.lower())
        self.assertEqual(notif.target_object_id, self.enrollment.pk)
