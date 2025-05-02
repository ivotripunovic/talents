from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from datetime import date
from .models import (
    PlayerProfile, CoachProfile, ScoutProfile, ManagerProfile,
    TrainerProfile, ClubProfile, FanProfile
)
from django.utils import timezone

User = get_user_model()

class BaseRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'date_of_birth', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

class PlayerRegistrationForm(BaseRegistrationForm):
    position = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    height = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    weight = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    preferred_foot = forms.ChoiceField(
        choices=[('', '---')] + [('LEFT', 'Left'), ('RIGHT', 'Right'), ('BOTH', 'Both')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    parent_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('position', 'height', 'weight', 'preferred_foot', 'parent_email')

    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        parent_email = cleaned_data.get('parent_email')

        if date_of_birth:
            today = timezone.now().date()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            cleaned_data['is_underage'] = age < 18

            if age < 18 and not parent_email:
                raise ValidationError('Parent/Guardian email is required for players under 18.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PLAYER
        if commit:
            user.save()
            # Update the profile created by the signal
            profile = user.player_profile
            profile.position = self.cleaned_data.get('position', '')
            profile.height = self.cleaned_data.get('height')
            profile.weight = self.cleaned_data.get('weight')
            profile.preferred_foot = self.cleaned_data.get('preferred_foot', '')

            # Handle parent/guardian relationship if player is underage
            if self.cleaned_data.get('is_underage'):
                parent_email = self.cleaned_data.get('parent_email')
                if parent_email:
                    # Create or get parent user account
                    parent_user, created = User.objects.get_or_create(
                        email=parent_email,
                        defaults={
                            'username': parent_email.split('@')[0],
                            'role': User.Role.FAN
                        }
                    )
                    if created:
                        # Set a random password for new parent accounts
                        random_password = User.objects.make_random_password()
                        parent_user.set_password(random_password)
                        parent_user.save()
                        # TODO: Send email to parent with their credentials

                    profile.parent_guardian = parent_user

            profile.save()
        return user

class CoachRegistrationForm(BaseRegistrationForm):
    coaching_license = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    experience_years = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    specialization = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    certifications = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('coaching_license', 'experience_years', 'specialization', 'certifications')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.COACH
        if commit:
            user.save()
            # Update the profile created by the signal
            profile = user.coach_profile
            profile.specialization = self.cleaned_data.get('specialization', '')
            profile.experience_years = self.cleaned_data.get('experience_years', 0)
            profile.certifications = self.cleaned_data.get('certifications', '')
            profile.save()
        return user

class ScoutRegistrationForm(BaseRegistrationForm):
    organization = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    regions_covered = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    years_of_experience = forms.IntegerField(
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('organization', 'regions_covered', 'years_of_experience')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.SCOUT
        if commit:
            user.save()
            profile = user.scout_profile
            profile.organization = self.cleaned_data.get('organization', '')
            profile.regions_covered = self.cleaned_data.get('regions_covered', '')
            profile.years_of_experience = self.cleaned_data['years_of_experience']
            profile.save()
        return user

class ManagerRegistrationForm(BaseRegistrationForm):
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    responsibilities = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('department', 'responsibilities')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.MANAGER
        if commit:
            user.save()
            # Update the profile created by the signal
            profile = user.manager_profile
            profile.department = self.cleaned_data.get('department', '')
            profile.responsibilities = self.cleaned_data.get('responsibilities', '')
            profile.save()
        return user

class TrainerRegistrationForm(BaseRegistrationForm):
    specialization = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    certifications = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    experience_years = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('specialization', 'certifications', 'experience_years')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.TRAINER
        if commit:
            user.save()
            # Update the profile created by the signal
            profile = user.trainer_profile
            profile.specialization = self.cleaned_data.get('specialization', '')
            profile.certifications = self.cleaned_data.get('certifications', '')
            profile.experience_years = self.cleaned_data.get('experience_years', 0)
            profile.save()
        return user

class ClubRegistrationForm(BaseRegistrationForm):
    club_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    founded_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    location = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    league = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('club_name', 'founded_year', 'location', 'league')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CLUB
        if commit:
            user.save()
            # Update the profile created by the signal
            profile = user.club_profile
            profile.club_name = self.cleaned_data.get('club_name', '')
            profile.founded_year = self.cleaned_data.get('founded_year')
            profile.location = self.cleaned_data.get('location', '')
            profile.league = self.cleaned_data.get('league', '')
            profile.save()
        return user

class FanRegistrationForm(BaseRegistrationForm):
    favorite_club = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    membership_type = forms.ChoiceField(
        choices=[('REGULAR', 'Regular'), ('PREMIUM', 'Premium'), ('VIP', 'VIP')],
        initial='REGULAR',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('favorite_club', 'membership_type')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.FAN
        if commit:
            user.save()
            # Update the profile created by the signal
            profile = user.fan_profile
            profile.favorite_club = self.cleaned_data.get('favorite_club', '')
            profile.membership_type = self.cleaned_data.get('membership_type', 'REGULAR')
            profile.save()
        return user 