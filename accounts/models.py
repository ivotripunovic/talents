from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

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

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

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
    is_verified = models.BooleanField(default=False)

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
    position = models.CharField(max_length=50, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in cm
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in kg
    preferred_foot = models.CharField(
        max_length=10,
        choices=[('LEFT', 'Left'), ('RIGHT', 'Right'), ('BOTH', 'Both')],
        blank=True
    )
    
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
