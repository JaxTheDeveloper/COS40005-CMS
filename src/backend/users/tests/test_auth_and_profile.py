from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AuthAndProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='student@example.com',
            password='testpass123',
            user_type='student'
        )

    def test_password_reset_sends_email(self):
        url = reverse('password_reset')
        resp = self.client.post(url, {'email': self.user.email})
        # PasswordResetView redirects to done page on success
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('password_reset_done'), resp['Location'])

    def test_profile_edit_requires_login_and_updates(self):
        edit_url = reverse('profile_edit')

        # Unauthenticated should redirect to login
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('login'), resp['Location'])

        # Login and submit profile changes
        self.client.login(email=self.user.email, password='testpass123')
        resp = self.client.post(edit_url, {
            'first_name': 'Alice',
            'last_name': 'Student',
            'phone_number': '+61400123456',
        }, follow=True)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Alice')
        self.assertEqual(self.user.last_name, 'Student')
