from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, TemplateView, UpdateView
from django.urls import reverse_lazy
from .forms import (
    PlayerRegistrationForm, CoachRegistrationForm, ScoutRegistrationForm,
    ManagerRegistrationForm, TrainerRegistrationForm, ClubRegistrationForm,
    FanRegistrationForm, PlayerProfileUpdateForm, ClubProfileUpdateForm
)
from django.template import TemplateDoesNotExist
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (
    ScoutProfile, PlayerProfile, CoachProfile, ManagerProfile,
    TrainerProfile, ClubProfile, FanProfile, EmailVerificationToken, ParentalConsentRequest
)
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.utils import timezone
from django import forms
from django.contrib.admin.views.decorators import staff_member_required

User = get_user_model()

class RoleSelectionView(TemplateView):
    template_name = 'accounts/role_selection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = [
            {
                'id': User.Role.PLAYER,
                'name': 'Player',
                'description': 'Register as a player to showcase your talents and connect with clubs.',
                'url': 'accounts:player_registration'
            },
            {
                'id': User.Role.COACH,
                'name': 'Coach',
                'description': 'Register as a coach to manage teams and develop players.',
                'url': 'accounts:coach_registration'
            },
            {
                'id': User.Role.SCOUT,
                'name': 'Scout',
                'description': 'Register as a scout to discover new talents.',
                'url': 'accounts:scout_registration'
            },
            {
                'id': User.Role.MANAGER,
                'name': 'Manager',
                'description': 'Register as a manager to oversee club operations.',
                'url': 'accounts:manager_registration'
            },
            {
                'id': User.Role.TRAINER,
                'name': 'Trainer',
                'description': 'Register as a trainer to provide specialized training.',
                'url': 'accounts:trainer_registration'
            },
            {
                'id': User.Role.CLUB,
                'name': 'Club',
                'description': 'Register your club to find talents and manage your team.',
                'url': 'accounts:club_registration'
            },
            {
                'id': User.Role.FAN,
                'name': 'Fan',
                'description': 'Register as a fan to follow your favorite players and clubs.',
                'url': 'accounts:fan_registration'
            },
        ]
        return context

class BaseRegistrationView(CreateView):
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        # Generate verification token
        token = EmailVerificationToken.generate_token(user)
        
        # Send verification email
        current_site = get_current_site(self.request)
        subject = 'Verify your email address'
        html_message = render_to_string('accounts/email/verify_email.html', {
            'user': user,
            'domain': current_site.domain,
            'token': token.token,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Don't log in the user until email is verified
        return response

class PlayerRegistrationView(BaseRegistrationView):
    template_name = 'accounts/registration/player.html'
    form_class = PlayerRegistrationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object  # Already saved by super().form_valid(form)
        # Only link parent/guardian if needed; do not call form.save() again
        if form.cleaned_data.get('is_underage'):
            parent_email = form.cleaned_data.get('parent_email')
            if parent_email:
                parent_user, created = User.objects.get_or_create(
                    email=parent_email,
                    defaults={
                        'username': parent_email.split('@')[0],
                        'role': User.Role.FAN,
                        'is_active': True
                    }
                )
                if created:
                    parent_user.set_password(User.objects.make_random_password())
                    parent_user.save()
                    messages.info(
                        self.request,
                        f"A password reset email will be sent to the parent/guardian at {parent_email}"
                    )
                user.player_profile.parent_guardian = parent_user
                user.player_profile.save()
        return response

class CoachRegistrationView(BaseRegistrationView):
    template_name = 'accounts/registration/coach.html'
    form_class = CoachRegistrationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class ScoutRegistrationView(BaseRegistrationView):
    template_name = 'accounts/registration/scout.html'
    form_class = ScoutRegistrationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class ManagerRegistrationView(BaseRegistrationView):
    template_name = 'accounts/registration/manager.html'
    form_class = ManagerRegistrationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class TrainerRegistrationView(BaseRegistrationView):
    template_name = 'accounts/registration/trainer.html'
    form_class = TrainerRegistrationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class ClubRegistrationView(BaseRegistrationView):
    template_name = 'accounts/registration/club.html'
    form_class = ClubRegistrationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class FanRegistrationView(BaseRegistrationView):
    template_name = 'accounts/registration/fan.html'
    form_class = FanRegistrationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class RegistrationSuccessView(TemplateView):
    template_name = 'accounts/registration/verification_sent.html'

@login_required
def profile_view(request):
    """Generic profile view that redirects to role-specific profile."""
    user = request.user
    role = user.role.lower()
    return redirect(f'accounts:{role}_profile')

@login_required
def player_profile_view(request):
    return render(request, 'accounts/profile/player.html', {
        'user': request.user,
        'profile': getattr(request.user, 'player_profile', None),
    })

@login_required
def coach_profile_view(request):
    return render(request, 'accounts/profile/coach.html', {'user': request.user})

@login_required
def scout_profile_view(request):
    return render(request, 'accounts/profile/scout.html', {'user': request.user})

@login_required
def manager_profile_view(request):
    return render(request, 'accounts/profile/manager.html', {'user': request.user})

@login_required
def trainer_profile_view(request):
    return render(request, 'accounts/profile/trainer.html', {'user': request.user})

@login_required
def club_profile_view(request):
    return render(request, 'accounts/profile/club.html', {'user': request.user})

@login_required
def fan_profile_view(request):
    return render(request, 'accounts/profile/fan.html', {'user': request.user})

class ScoutProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = ScoutProfile
    template_name = 'accounts/profile/scout_update.html'
    fields = ['organization', 'regions_covered', 'years_of_experience']
    success_url = reverse_lazy('accounts:scout_profile')

    def get_object(self, queryset=None):
        return self.request.user.scout_profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class PlayerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = PlayerProfile
    template_name = 'accounts/profile/player_update.html'
    form_class = PlayerProfileUpdateForm
    success_url = reverse_lazy('accounts:player_profile')

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user.player_profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

class CoachProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CoachProfile
    template_name = 'accounts/profile/coach_update.html'
    fields = ['specialization', 'experience_years', 'certifications']
    success_url = reverse_lazy('accounts:coach_profile')

    def get_object(self, queryset=None):
        return self.request.user.coach_profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class ManagerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = ManagerProfile
    template_name = 'accounts/profile/manager_update.html'
    fields = ['current_club', 'years_of_experience', 'specialization', 'achievements']
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user.manager_profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class TrainerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = TrainerProfile
    template_name = 'accounts/profile/trainer_update.html'
    fields = ['specialization', 'years_of_experience', 'certifications', 'current_club', 'training_focus', 'available_for_hire', 'achievements', 'training_methodology']
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user.trainer_profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class ClubProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = ClubProfile
    template_name = 'accounts/profile/club_update.html'
    form_class = ClubProfileUpdateForm
    success_url = reverse_lazy('accounts:club_profile')

    def get_object(self, queryset=None):
        return self.request.user.club_profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class FanProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = FanProfile
    template_name = 'accounts/profile/fan_update.html'
    fields = ['favorite_team', 'fan_since', 'season_ticket_holder']
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user.fan_profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

def verify_email(request, token):
    verification = get_object_or_404(EmailVerificationToken, token=token)
    if verification.is_valid():
        user = verification.user
        user.is_active = True
        user.email_verified = True
        user.save()
        verification.used = True
        verification.save()
        messages.success(request, 'Your email has been verified successfully!')
        return redirect('accounts:login')
    else:
        if verification.used:
            error_message = 'This verification link has already been used.'
        else:
            error_message = 'This verification link has expired.'
        return render(request, 'accounts/email/verification_error.html', {'error_message': error_message}, status=400)

def consent_verify_view(request, token):
    consent = get_object_or_404(ParentalConsentRequest, token=token)
    class ConsentForm(forms.Form):
        action = forms.ChoiceField(choices=[('grant', 'Grant Consent'), ('reject', 'Reject Consent')], widget=forms.RadioSelect)
        notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    message = None
    if request.method == 'POST' and consent.status == 'pending':
        form = ConsentForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            consent.status = 'granted' if action == 'grant' else 'rejected'
            consent.responded_at = timezone.now()
            consent.response_ip = request.META.get('REMOTE_ADDR')
            consent.notes = form.cleaned_data['notes']
            consent.save()
            message = 'Consent has been {}.'.format('granted' if action == 'grant' else 'rejected')
    else:
        form = ConsentForm()
    return render(request, 'accounts/consent_verify.html', {
        'consent': consent,
        'form': form,
        'message': message,
    })

@staff_member_required
def parental_consent_list_view(request):
    status = request.GET.get('status')
    qs = ParentalConsentRequest.objects.all().order_by('-requested_at')
    if status:
        qs = qs.filter(status=status)
    return render(request, 'accounts/parental_consent_list.html', {
        'requests': qs,
        'status': status,
    })
