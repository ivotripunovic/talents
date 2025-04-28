from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import (
    PlayerProfile, CoachProfile, ScoutProfile,
    ManagerProfile, TrainerProfile, ClubProfile, FanProfile
)

# Create your tests here.

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
