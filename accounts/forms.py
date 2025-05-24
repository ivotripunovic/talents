from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from datetime import date
from .models import (
    PlayerProfile, CoachProfile, ScoutProfile, ManagerProfile,
    TrainerProfile, ClubProfile, FanProfile, ParentalConsentRequest
)
from django.utils import timezone
from .utils import send_parental_consent_email

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
        self.request = kwargs.pop('request', None)
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
    parent_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    parent_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    parent_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('position', 'height', 'weight', 'preferred_foot', 'parent_name', 'parent_email', 'parent_phone')

    def clean(self):
        cleaned_data = super().clean()
        date_of_birth = cleaned_data.get('date_of_birth')
        parent_name = cleaned_data.get('parent_name')
        parent_email = cleaned_data.get('parent_email')
        parent_phone = cleaned_data.get('parent_phone')
        if date_of_birth:
            today = timezone.now().date()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            cleaned_data['is_underage'] = age < 18
            if age < 18:
                if not parent_name:
                    self.add_error('parent_name', 'Parent/Guardian name is required for players under 18.')
                if not parent_email:
                    self.add_error('parent_email', 'Parent/Guardian email is required for players under 18.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PLAYER
        if commit:
            user.save()
            profile = user.player_profile
            profile.position = self.cleaned_data.get('position', '')
            profile.height = self.cleaned_data.get('height')
            profile.weight = self.cleaned_data.get('weight')
            profile.preferred_foot = self.cleaned_data.get('preferred_foot', '')
            positions_str = self.data.get('positions') or self.cleaned_data.get('positions')
            if positions_str:
                profile.set_positions([p for p in positions_str.split(',') if p])
            else:
                profile.set_positions([])
            # Parental consent workflow
            if self.cleaned_data.get('is_underage'):
                consent = ParentalConsentRequest.objects.create(
                    player=user,
                    parent_name=self.cleaned_data.get('parent_name'),
                    parent_email=self.cleaned_data.get('parent_email'),
                    parent_phone=self.cleaned_data.get('parent_phone'),
                )
                profile.parental_consent_status = 'pending'
                if self.request:
                    send_parental_consent_email(
                        parent_email=self.cleaned_data.get('parent_email'),
                        parent_name=self.cleaned_data.get('parent_name'),
                        player=user,
                        token=consent.token,
                        request=self.request
                    )
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

class PlayerProfileUpdateForm(forms.ModelForm):
    positions = forms.CharField(required=False, widget=forms.HiddenInput())
    parent_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    parent_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    parent_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = PlayerProfile
        fields = ['country', 'city', 'age', 'height', 'weight', 'preferred_foot', 'positions', 'parent_name', 'parent_email', 'parent_phone']
        widgets = {
            'preferred_foot': forms.Select(choices=[('', '---'), ('LEFT', 'Left'), ('RIGHT', 'Right'), ('BOTH', 'Both')]),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Pre-populate positions field from model
        if self.instance and self.instance.positions:
            self.fields['positions'].initial = self.instance.positions
        # Pre-populate parent fields from latest consent request if exists
        latest_consent = self.instance.user.parental_consent_requests.order_by('-requested_at').first() if self.instance and getattr(self.instance, 'user', None) else None
        if latest_consent:
            self.fields['parent_name'].initial = latest_consent.parent_name
            self.fields['parent_email'].initial = latest_consent.parent_email
            self.fields['parent_phone'].initial = latest_consent.parent_phone

    def clean(self):
        cleaned_data = super().clean()
        user = getattr(self.instance, 'user', None)
        date_of_birth = getattr(user, 'date_of_birth', None)
        parent_name = cleaned_data.get('parent_name')
        parent_email = cleaned_data.get('parent_email')
        parent_phone = cleaned_data.get('parent_phone')
        if date_of_birth:
            today = timezone.now().date()
            age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
            cleaned_data['is_underage'] = age < 18
            if age < 18:
                if not parent_name:
                    self.add_error('parent_name', 'Parent/Guardian name is required for players under 18.')
                if not parent_email:
                    self.add_error('parent_email', 'Parent/Guardian email is required for players under 18.')
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        positions_str = self.data.get('positions', '')
        if positions_str:
            profile.set_positions([p for p in positions_str.split(',') if p])
        else:
            profile.set_positions([])
        if commit:
            profile.save()
            # Parental consent workflow
            if self.cleaned_data.get('is_underage') and self.cleaned_data.get('parent_email'):
                consent = ParentalConsentRequest.objects.create(
                    player=profile.user,
                    parent_name=self.cleaned_data.get('parent_name'),
                    parent_email=self.cleaned_data.get('parent_email'),
                    parent_phone=self.cleaned_data.get('parent_phone'),
                )
                profile.parental_consent_status = 'pending'
                if self.request:
                    send_parental_consent_email(
                        parent_email=self.cleaned_data.get('parent_email'),
                        parent_name=self.cleaned_data.get('parent_name'),
                        player=profile.user,
                        token=consent.token,
                        request=self.request
                    )
                profile.save()
        return profile 