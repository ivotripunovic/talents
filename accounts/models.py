from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid

class CustomUserManager(BaseUserManager):
    def _create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'MANAGER')  # Set default role for superuser

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

    def make_random_password(self, length=10, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'):
        """
        Generate a random password with the given length and allowed characters.
        """
        from django.utils.crypto import get_random_string
        return get_random_string(length, allowed_chars)

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        PLAYER = 'PLAYER', _('Player')
        COACH = 'COACH', _('Coach')
        SCOUT = 'SCOUT', _('Scout')
        MANAGER = 'MANAGER', _('Manager')
        TRAINER = 'TRAINER', _('Trainer')
        CLUB = 'CLUB', _('Club')
        FAN = 'FAN', _('Fan')
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.FAN
    )
    date_of_birth = models.DateField(null=True, blank=True)
    email_verified = models.BooleanField(
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    is_active = models.BooleanField(
        default=False,  # Changed from True to False - users must verify email
        help_text=_('Designates whether this user should be treated as active. '
                   'Users must verify their email address to become active.')
    )

    # Add related_name to fix reverse accessor clash
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'role']

    def __str__(self):
        return f"{self.email} - {self.role}"

class PlayerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='player_profile')
    parent_guardian = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guardian_of'
    )
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in cm
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in kg
    PREFERRED_FOOT_CHOICES = [
        ('LEFT', 'Left'),
        ('RIGHT', 'Right'),
        ('BOTH', 'Both'),
    ]
    preferred_foot = models.CharField(max_length=10, choices=PREFERRED_FOOT_CHOICES, blank=True)
    positions = models.CharField(max_length=200, blank=True, help_text='Comma-separated position codes (e.g. GK,CB,LB)')
    languages = models.CharField(max_length=200, blank=True, help_text='Comma-separated language codes (e.g. en,hr,de)')
    club = models.CharField(max_length=100, blank=True)
    achievements = models.JSONField(null=True, blank=True)
    medical_info = models.JSONField(null=True, blank=True)
    social_links = models.JSONField(null=True, blank=True)
    privacy_settings = models.JSONField(null=True, blank=True)
    VERIFICATION_STATUS_CHOICES = [
        ('unverified', 'Unverified'),
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='unverified')
    PARENTAL_CONSENT_CHOICES = [
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('granted', 'Granted'),
        ('rejected', 'Rejected'),
    ]
    parental_consent_status = models.CharField(max_length=20, choices=PARENTAL_CONSENT_CHOICES, default='not_required')

    def set_positions(self, positions_list):
        self.positions = ','.join(positions_list)

    def get_positions(self):
        if not self.positions:
            return []
        return self.positions.split(',')

    def set_languages(self, languages_list):
        self.languages = ','.join(languages_list)

    def get_languages(self):
        if not self.languages:
            return []
        return self.languages.split(',')
    
    def __str__(self):
        return f"Player Profile - {self.user.email}"

class CoachProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='coach_profile')
    specialization = models.CharField(max_length=100, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    certifications = models.TextField(blank=True)
    
    def __str__(self):
        return f"Coach Profile - {self.user.email}"

class ScoutProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='scout_profile')
    organization = models.CharField(max_length=100, blank=True)
    regions_covered = models.TextField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Scout Profile - {self.user.email}"

class ManagerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='manager_profile')
    department = models.CharField(max_length=100, blank=True)
    responsibilities = models.TextField(blank=True)
    
    def __str__(self):
        return f"Manager Profile - {self.user.email}"

class TrainerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='trainer_profile')
    specialization = models.CharField(max_length=100, blank=True)
    certifications = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Trainer Profile - {self.user.email}"

class ClubProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='club_profile')
    club_name = models.CharField(max_length=100)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    league = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Club Profile - {self.club_name}"

class FanProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='fan_profile')
    favorite_club = models.CharField(max_length=100, blank=True)
    membership_type = models.CharField(
        max_length=20,
        choices=[
            ('REGULAR', 'Regular'),
            ('PREMIUM', 'Premium'),
            ('VIP', 'VIP')
        ],
        default='REGULAR'
    )
    
    def __str__(self):
        return f"Fan Profile - {self.user.email}"

class EmailVerificationToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration to 7 days from creation
            self.expires_at = timezone.now() + timezone.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    @classmethod
    def generate_token(cls, user):
        # Delete any existing unused tokens for this user
        cls.objects.filter(user=user, is_used=False).delete()
        # Create new token
        return cls.objects.create(user=user)
