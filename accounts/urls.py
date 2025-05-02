from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration URLs
    path('register/', views.RoleSelectionView.as_view(), name='register'),
    path('register/player/', views.PlayerRegistrationView.as_view(), name='player_registration'),
    path('register/coach/', views.CoachRegistrationView.as_view(), name='coach_registration'),
    path('register/scout/', views.ScoutRegistrationView.as_view(), name='scout_registration'),
    path('register/manager/', views.ManagerRegistrationView.as_view(), name='manager_registration'),
    path('register/trainer/', views.TrainerRegistrationView.as_view(), name='trainer_registration'),
    path('register/club/', views.ClubRegistrationView.as_view(), name='club_registration'),
    path('register/fan/', views.FanRegistrationView.as_view(), name='fan_registration'),
    path('register/success/', views.RegistrationSuccessView.as_view(), name='registration_success'),
    
    # Email Verification URL
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),
    
    # Password Reset URLs
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset/form.html',
             email_template_name='accounts/password_reset/email.html',
             subject_template_name='accounts/password_reset/subject.txt'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset/done.html'
         ),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset/confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset/complete.html'
         ),
         name='password_reset_complete'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),  # Generic profile router
    path('profile/player/', views.player_profile_view, name='player_profile'),
    path('profile/coach/', views.coach_profile_view, name='coach_profile'),
    path('profile/scout/', views.scout_profile_view, name='scout_profile'),
    path('profile/manager/', views.manager_profile_view, name='manager_profile'),
    path('profile/trainer/', views.trainer_profile_view, name='trainer_profile'),
    path('profile/club/', views.club_profile_view, name='club_profile'),
    path('profile/fan/', views.fan_profile_view, name='fan_profile'),
    
    # Profile Update URLs
    path('profile/player/update/', views.PlayerProfileUpdateView.as_view(), name='player_profile_update'),
    path('profile/coach/update/', views.CoachProfileUpdateView.as_view(), name='coach_profile_update'),
    path('profile/scout/update/', views.ScoutProfileUpdateView.as_view(), name='scout_profile_update'),
    path('profile/manager/update/', views.ManagerProfileUpdateView.as_view(), name='manager_profile_update'),
    path('profile/trainer/update/', views.TrainerProfileUpdateView.as_view(), name='trainer_profile_update'),
    path('profile/club/update/', views.ClubProfileUpdateView.as_view(), name='club_profile_update'),
    path('profile/fan/update/', views.FanProfileUpdateView.as_view(), name='fan_profile_update'),
] 