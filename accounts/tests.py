from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    PlayerProfile, CoachProfile, ScoutProfile,
    ManagerProfile, TrainerProfile, ClubProfile, FanProfile
)

# Create your tests here.

User = get_user_model()

class BaseRegistrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.base_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'date_of_birth': (timezone.now() - timedelta(days=365*25)).date().isoformat()  # 25 years old
        }

    def assertFormErrorMessage(self, response, field, message):
        """Assert that a form error message exists for a field."""
        form = response.context['form']
        self.assertIn(field, form.errors)
        self.assertIn(message, form.errors[field][0])

class PlayerRegistrationTest(BaseRegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('accounts:player_registration')
        self.data = {
            **self.base_data,
            'position': 'Forward',
            'height': '180.5',
            'weight': '75.5',
            'preferred_foot': 'RIGHT'
        }

    def test_player_registration_success(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)  # Should redirect after success
        
        # Verify user was created
        user = User.objects.get(username=self.data['username'])
        self.assertEqual(user.role, User.Role.PLAYER)
        
        # Verify profile was created
        profile = user.player_profile
        self.assertEqual(profile.position, self.data['position'])
        self.assertEqual(float(profile.height), float(self.data['height']))
        self.assertEqual(float(profile.weight), float(self.data['weight']))
        self.assertEqual(profile.preferred_foot, self.data['preferred_foot'])

    def test_underage_player_registration(self):
        underage_data = {
            **self.data,
            'date_of_birth': (timezone.now() - timedelta(days=365*15)).date().isoformat(),  # 15 years old
            'parent_email': 'parent@example.com'
        }
        
        response = self.client.post(self.url, underage_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify user and profile were created
        user = User.objects.get(username=underage_data['username'])
        self.assertEqual(user.role, User.Role.PLAYER)
        
        # Verify parent account was created
        parent = User.objects.get(email=underage_data['parent_email'])
        self.assertEqual(parent.role, User.Role.FAN)
        
        # Verify parent-child relationship
        profile = user.player_profile
        self.assertEqual(profile.parent_guardian, parent)

    def test_underage_player_without_parent_email(self):
        underage_data = {
            **self.data,
            'date_of_birth': (timezone.now() - timedelta(days=365*15)).date().isoformat(),  # 15 years old
        }
        
        response = self.client.post(self.url, underage_data)
        self.assertEqual(response.status_code, 200)  # Should stay on form
        self.assertFormErrorMessage(response, None, 'Parent/Guardian email is required for players under 18.')

class CoachRegistrationTest(BaseRegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('accounts:coach_registration')
        self.data = {
            **self.base_data,
            'coaching_license': 'UEFA A',
            'experience_years': 5,
            'specialization': 'Youth Development',
            'certifications': 'UEFA A License, Youth Coach Certificate'
        }

    def test_coach_registration_success(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(username=self.data['username'])
        self.assertEqual(user.role, User.Role.COACH)
        
        profile = user.coach_profile
        self.assertEqual(profile.specialization, self.data['specialization'])
        self.assertEqual(profile.experience_years, self.data['experience_years'])
        self.assertEqual(profile.certifications, self.data['certifications'])

class ScoutRegistrationTest(BaseRegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('accounts:scout_registration')
        self.data = {
            **self.base_data,
            'organization': 'Top Talent Scouts Ltd',
            'regions_covered': 'Europe, South America',
            'years_of_experience': 8
        }

    def test_scout_registration_success(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)  # Should redirect after success
        
        user = User.objects.get(username=self.data['username'])
        self.assertEqual(user.role, User.Role.SCOUT)
        
        profile = user.scout_profile
        self.assertEqual(profile.organization, self.data['organization'])
        self.assertEqual(profile.regions_covered, self.data['regions_covered'])
        self.assertEqual(profile.years_of_experience, self.data['years_of_experience'])

    def test_scout_registration_missing_required_fields(self):
        # Test with missing years_of_experience
        data = {**self.data}
        data.pop('years_of_experience')
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)  # Should stay on form
        self.assertFormErrorMessage(response, 'years_of_experience', 'This field is required.')

    def test_scout_registration_invalid_years(self):
        # Test with negative years of experience
        data = {**self.data, 'years_of_experience': -1}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormErrorMessage(response, 'years_of_experience', 'Ensure this value is greater than or equal to 0.')

    def test_scout_registration_form_display(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/registration/scout.html')
        self.assertContains(response, 'Scout Registration')
        self.assertContains(response, 'Regions covered')  # Exact match
        self.assertContains(response, 'Organization')  # Exact match
        self.assertContains(response, 'Years of experience')  # Exact match

class ScoutProfileTest(BaseRegistrationTestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'username': 'testscout',
            'email': 'scout@example.com',
            'password': 'testpass123',
            'role': User.Role.SCOUT
        }
        self.user = User.objects.create_user(**self.user_data)
        self.profile_data = {
            'organization': 'Elite Scouts Inc',
            'regions_covered': 'North America, Asia',
            'years_of_experience': 10
        }
        self.profile = self.user.scout_profile
        for key, value in self.profile_data.items():
            setattr(self.profile, key, value)
        self.profile.save()
        self.client.login(username=self.user_data['email'], password=self.user_data['password'])

    def test_profile_page_access(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile/scout.html')

    def test_profile_page_content(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.profile_data['organization'])
        self.assertContains(response, self.profile_data['regions_covered'])
        self.assertContains(response, str(self.profile_data['years_of_experience']))

    def test_profile_page_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:profile')}")

    def test_profile_update(self):
        update_url = reverse('accounts:update_profile')
        new_data = {
            'organization': 'Global Talent Hunters',
            'regions_covered': 'Europe, Africa',
            'years_of_experience': 12
        }
        response = self.client.post(update_url, new_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after success
        
        # Refresh profile from database
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.organization, new_data['organization'])
        self.assertEqual(self.profile.regions_covered, new_data['regions_covered'])
        self.assertEqual(self.profile.years_of_experience, new_data['years_of_experience'])

    def test_profile_update_invalid_data(self):
        update_url = reverse('accounts:update_profile')
        invalid_data = {
            'organization': 'Global Talent Hunters',
            'regions_covered': 'Europe, Africa',
            'years_of_experience': -1  # Invalid negative value
        }
        response = self.client.post(update_url, invalid_data)
        self.assertEqual(response.status_code, 200)  # Should stay on form
        self.assertFormErrorMessage(response, 'years_of_experience', 'Ensure this value is greater than or equal to 0.')

class ManagerRegistrationTest(BaseRegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('accounts:manager_registration')
        self.data = {
            **self.base_data,
            'department': 'Youth Academy',
            'responsibilities': 'Managing youth development program'
        }

    def test_manager_registration_success(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(username=self.data['username'])
        self.assertEqual(user.role, User.Role.MANAGER)
        
        profile = user.manager_profile
        self.assertEqual(profile.department, self.data['department'])
        self.assertEqual(profile.responsibilities, self.data['responsibilities'])

class TrainerRegistrationTest(BaseRegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('accounts:trainer_registration')
        self.data = {
            **self.base_data,
            'specialization': 'Strength and Conditioning',
            'certifications': 'NSCA-CSCS, FIFA Fitness Coach',
            'experience_years': 6
        }

    def test_trainer_registration_success(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(username=self.data['username'])
        self.assertEqual(user.role, User.Role.TRAINER)
        
        profile = user.trainer_profile
        self.assertEqual(profile.specialization, self.data['specialization'])
        self.assertEqual(profile.certifications, self.data['certifications'])
        self.assertEqual(profile.experience_years, self.data['experience_years'])

class ClubRegistrationTest(BaseRegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('accounts:club_registration')
        self.data = {
            **self.base_data,
            'club_name': 'FC Test United',
            'founded_year': 1990,
            'location': 'Test City, Country',
            'league': 'Premier League'
        }

    def test_club_registration_success(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(username=self.data['username'])
        self.assertEqual(user.role, User.Role.CLUB)
        
        profile = user.club_profile
        self.assertEqual(profile.club_name, self.data['club_name'])
        self.assertEqual(profile.founded_year, self.data['founded_year'])
        self.assertEqual(profile.location, self.data['location'])
        self.assertEqual(profile.league, self.data['league'])

class FanRegistrationTest(BaseRegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('accounts:fan_registration')
        self.data = {
            **self.base_data,
            'favorite_club': 'FC Test United',
            'membership_type': 'PREMIUM'
        }

    def test_fan_registration_success(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(username=self.data['username'])
        self.assertEqual(user.role, User.Role.FAN)
        
        profile = user.fan_profile
        self.assertEqual(profile.favorite_club, self.data['favorite_club'])
        self.assertEqual(profile.membership_type, self.data['membership_type'])

class CommonRegistrationTests(BaseRegistrationTestCase):
    def setUp(self):
        super().setUp()
        self.urls = {
            'player': reverse('accounts:player_registration'),
            'coach': reverse('accounts:coach_registration'),
            'scout': reverse('accounts:scout_registration'),
            'manager': reverse('accounts:manager_registration'),
            'trainer': reverse('accounts:trainer_registration'),
            'club': reverse('accounts:club_registration'),
            'fan': reverse('accounts:fan_registration'),
        }

    def test_password_validation(self):
        for role, url in self.urls.items():
            data = {**self.base_data, 'password1': 'short', 'password2': 'short'}
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)
            self.assertFormErrorMessage(response, 'password2', 
                               'This password is too short. It must contain at least 8 characters.')

    def test_email_validation(self):
        for role, url in self.urls.items():
            data = {**self.base_data, 'email': 'invalid-email'}
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)
            self.assertFormErrorMessage(response, 'email', 'Enter a valid email address.')

    def test_required_fields(self):
        required_fields = ['username', 'email', 'password1', 'password2', 'date_of_birth']
        for role, url in self.urls.items():
            for field in required_fields:
                data = {**self.base_data}
                data.pop(field)
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, 200)
                self.assertFormErrorMessage(response, field, 'This field is required.')

class CustomUserTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': 'PLAYER'
        }

    def test_create_user(self):
        user = self.User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.role, self.user_data['role'])
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        # Test that player profile was automatically created
        self.assertTrue(hasattr(user, 'player_profile'))

    def test_create_superuser(self):
        admin_user = self.User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='MANAGER'
        )
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        # Test that manager profile was automatically created
        self.assertTrue(hasattr(admin_user, 'manager_profile'))

class PlayerProfileTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='player',
            email='player@example.com',
            password='player123',
            role='PLAYER'
        )
        self.parent = self.User.objects.create_user(
            username='parent',
            email='parent@example.com',
            password='parent123',
            role='FAN'
        )

    def test_update_player_profile(self):
        # Profile is already created by signal, just update it
        profile = self.user.player_profile
        profile.position = 'Forward'
        profile.height = 180.5
        profile.weight = 75.5
        profile.preferred_foot = 'RIGHT'
        profile.parent_guardian = self.parent
        profile.save()

        # Refresh from database
        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.position, 'Forward')
        self.assertEqual(float(profile.height), 180.5)
        self.assertEqual(float(profile.weight), 75.5)
        self.assertEqual(profile.preferred_foot, 'RIGHT')
        self.assertEqual(profile.parent_guardian, self.parent)

class CoachProfileTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='coach',
            email='coach@example.com',
            password='coach123',
            role='COACH'
        )

    def test_update_coach_profile(self):
        # Profile is already created by signal, just update it
        profile = self.user.coach_profile
        profile.specialization = 'Youth Development'
        profile.experience_years = 10
        profile.certifications = 'UEFA Pro License'
        profile.save()

        # Refresh from database
        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.specialization, 'Youth Development')
        self.assertEqual(profile.experience_years, 10)
        self.assertEqual(profile.certifications, 'UEFA Pro License')

class ClubProfileTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='club',
            email='club@example.com',
            password='club123',
            role='CLUB'
        )

    def test_update_club_profile(self):
        # Profile is already created by signal, just update it
        profile = self.user.club_profile
        profile.club_name = 'Test FC'
        profile.founded_year = 1900
        profile.location = 'Test City'
        profile.league = 'Premier League'
        profile.save()

        # Refresh from database
        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.club_name, 'Test FC')
        self.assertEqual(profile.founded_year, 1900)
        self.assertEqual(profile.location, 'Test City')
        self.assertEqual(profile.league, 'Premier League')
