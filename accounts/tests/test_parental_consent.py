from django.test import TestCase, override_settings, Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from accounts.models import PlayerProfile, ParentalConsentRequest
from datetime import date, timedelta
from django.utils import timezone

User = get_user_model()

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ParentalConsentWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.underage_dob = date.today() - timedelta(days=365*10)  # 10 years old
        self.parent_email = 'parent@example.com'
        self.parent_name = 'Parent Test'
        self.parent_phone = '1234567890'

    def test_consent_request_created_on_registration(self):
        resp = self.client.post(reverse('accounts:player_registration'), {
            'username': 'underage',
            'email': 'underage@example.com',
            'date_of_birth': self.underage_dob,
            'password1': 'testpass123',
            'password2': 'testpass123',
            'parent_name': self.parent_name,
            'parent_email': self.parent_email,
            'parent_phone': self.parent_phone,
        })
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(email='underage@example.com')
        self.assertEqual(user.player_profile.parental_consent_status, 'pending')
        consents = ParentalConsentRequest.objects.filter(player=user)
        self.assertEqual(consents.count(), 1)
        consent = consents.first()
        self.assertEqual(consent.parent_email, self.parent_email)
        self.assertEqual(consent.status, 'pending')
        # Check that a parental consent email was sent
        found = any('Parental Consent Request' in m.subject for m in mail.outbox)
        self.assertTrue(found, 'Parental Consent Request email not found in outbox')
        self.assertIn(str(consent.token), ''.join(m.body for m in mail.outbox))

    def test_consent_request_created_on_profile_update(self):
        user = User.objects.create_user(username='underage2', email='underage2@example.com', password='testpass123', date_of_birth=self.underage_dob, role=User.Role.PLAYER)
        user.is_active = True
        if hasattr(user, 'email_verified'):
            user.email_verified = True
        user.save()
        self.client.login(username='underage2@example.com', password='testpass123')
        # Print and assert user is underage
        today = date.today()
        age = today.year - user.date_of_birth.year - ((today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day))
        assert age < 18, f"User should be underage, got age {age}"
        url = reverse('accounts:player_profile_update')
        resp = self.client.post(url, {
            'country': 'Testland',
            'city': 'Test City',
            'age': 10,
            'height': 140,
            'weight': 35,
            'preferred_foot': 'RIGHT',
            'positions': 'GK',
            'parent_name': self.parent_name,
            'parent_email': self.parent_email,
            'parent_phone': self.parent_phone,
        })
        consents = ParentalConsentRequest.objects.filter(player=user)
        self.assertEqual(consents.count(), 1)
        consent = consents.first()
        self.assertEqual(consent.parent_email, self.parent_email)
        self.assertEqual(consent.status, 'pending')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(consent.token), mail.outbox[0].body)

    def test_consent_verification_view_grant(self):
        user = User.objects.create_user(username='underage3', email='underage3@example.com', password='testpass123', date_of_birth=self.underage_dob, role=User.Role.PLAYER)
        consent = ParentalConsentRequest.objects.create(player=user, parent_name=self.parent_name, parent_email=self.parent_email, parent_phone=self.parent_phone)
        url = reverse('accounts:consent_verify', args=[consent.token])
        resp = self.client.post(url, {'action': 'grant', 'notes': 'Approved.'})
        self.assertContains(resp, 'Consent has been granted')
        consent.refresh_from_db()
        self.assertEqual(consent.status, 'granted')
        self.assertIsNotNone(consent.responded_at)
        self.assertEqual(consent.notes, 'Approved.')

    def test_consent_verification_view_reject(self):
        user = User.objects.create_user(username='underage4', email='underage4@example.com', password='testpass123', date_of_birth=self.underage_dob, role=User.Role.PLAYER)
        consent = ParentalConsentRequest.objects.create(player=user, parent_name=self.parent_name, parent_email=self.parent_email, parent_phone=self.parent_phone)
        url = reverse('accounts:consent_verify', args=[consent.token])
        resp = self.client.post(url, {'action': 'reject', 'notes': 'Not allowed.'})
        self.assertContains(resp, 'Consent has been rejected')
        consent.refresh_from_db()
        self.assertEqual(consent.status, 'rejected')
        self.assertEqual(consent.notes, 'Not allowed.')

    def test_consent_status_display_on_profile(self):
        user = User.objects.create_user(username='underage5', email='underage5@example.com', password='testpass123', date_of_birth=self.underage_dob, role=User.Role.PLAYER)
        user.is_active = True
        if hasattr(user, 'email_verified'):
            user.email_verified = True
        user.save()
        user.player_profile.parental_consent_status = 'pending'
        user.player_profile.save()
        self.client.login(username='underage5@example.com', password='testpass123')
        url = reverse('accounts:player_profile')
        resp = self.client.get(url)
        self.assertContains(resp, 'Parental Consent Status')
        self.assertContains(resp, 'pending')

    def test_admin_dashboard_lists_consent_requests(self):
        admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpass')
        user = User.objects.create_user(username='underage6', email='underage6@example.com', password='testpass123', date_of_birth=self.underage_dob, role=User.Role.PLAYER)
        ParentalConsentRequest.objects.create(player=user, parent_name=self.parent_name, parent_email=self.parent_email, parent_phone=self.parent_phone)
        self.client.login(username='admin@example.com', password='adminpass')
        url = reverse('accounts:parental_consent_list')
        resp = self.client.get(url)
        self.assertContains(resp, 'Parental Consent Requests')
        self.assertContains(resp, user.email)
        self.assertContains(resp, self.parent_email) 