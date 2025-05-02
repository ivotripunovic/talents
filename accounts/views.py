from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, TemplateView, UpdateView
from django.urls import reverse_lazy
from .forms import (
    PlayerRegistrationForm, CoachRegistrationForm, ScoutRegistrationForm,
    ManagerRegistrationForm, TrainerRegistrationForm, ClubRegistrationForm,
    FanRegistrationForm
)
from django.template import TemplateDoesNotExist
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import (
    ScoutProfile, PlayerProfile, CoachProfile, ManagerProfile,
    TrainerProfile, ClubProfile, FanProfile
)

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

class PlayerRegistrationView(CreateView):
    template_name = 'accounts/registration/player.html'
    form_class = PlayerRegistrationForm
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        
        # Handle parent/guardian relationship if player is underage
        if form.cleaned_data.get('is_underage'):
            parent_email = form.cleaned_data.get('parent_email')
            if parent_email:
                # Create or get parent user account
                parent_user, created = User.objects.get_or_create(
                    email=parent_email,
                    defaults={
                        'username': parent_email.split('@')[0],
                        'role': User.Role.FAN,
                        'is_active': True
                    }
                )
                if created:
                    # Set a random password and send reset password email
                    parent_user.set_password(User.objects.make_random_password())
                    parent_user.save()
                    # Send password reset email to parent
                    messages.info(
                        self.request,
                        f"A password reset email will be sent to the parent/guardian at {parent_email}"
                    )
                
                # Link parent to player profile
                user.player_profile.parent_guardian = parent_user
                user.player_profile.save()
        
        login(self.request, user)
        return response

class CoachRegistrationView(CreateView):
    template_name = 'accounts/registration/coach.html'
    form_class = CoachRegistrationForm
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class ScoutRegistrationView(CreateView):
    template_name = 'accounts/registration/scout.html'
    form_class = ScoutRegistrationForm
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class ManagerRegistrationView(CreateView):
    template_name = 'accounts/registration/manager.html'
    form_class = ManagerRegistrationForm
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class TrainerRegistrationView(CreateView):
    template_name = 'accounts/registration/trainer.html'
    form_class = TrainerRegistrationForm
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class ClubRegistrationView(CreateView):
    template_name = 'accounts/registration/club.html'
    form_class = ClubRegistrationForm
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class FanRegistrationView(CreateView):
    template_name = 'accounts/registration/fan.html'
    form_class = FanRegistrationForm
    success_url = reverse_lazy('accounts:registration_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class RegistrationSuccessView(TemplateView):
    template_name = 'accounts/registration/success.html'

@login_required
def profile_view(request):
    user = request.user
    role = user.role.lower()
    template_name = f'accounts/profile/{role}.html'
    
    try:
        return render(request, template_name, {'user': user})
    except TemplateDoesNotExist:
        messages.error(request, f"Profile template for {role} role not found.")
        return redirect('home')

class ScoutProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = ScoutProfile
    template_name = 'accounts/profile/scout_update.html'
    fields = ['organization', 'regions_covered', 'years_of_experience']
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user.scout_profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class PlayerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = PlayerProfile
    template_name = 'accounts/profile/player_update.html'
    fields = ['date_of_birth', 'position', 'height', 'weight', 'preferred_foot', 'current_club']
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user.player_profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class CoachProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CoachProfile
    template_name = 'accounts/profile/coach_update.html'
    fields = ['current_club', 'coaching_license', 'years_of_experience', 'preferred_formation', 'coaching_philosophy']
    success_url = reverse_lazy('accounts:profile')

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
    fields = ['founded_year', 'league', 'stadium', 'website', 'description', 'achievements']
    success_url = reverse_lazy('accounts:profile')

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
