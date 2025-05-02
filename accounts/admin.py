from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, PlayerProfile, CoachProfile, ScoutProfile,
    ManagerProfile, TrainerProfile, ClubProfile, FanProfile
)

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'role', 'email_verified', 'is_staff')
    list_filter = ('role', 'email_verified', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'date_of_birth')}),
        ('Permissions', {'fields': ('role', 'email_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'country', 'city', 'age', 'height', 'weight', 'preferred_foot', 'parent_guardian')
    list_filter = ('country', 'city', 'preferred_foot')
    search_fields = ('user__email', 'user__username', 'country', 'city')

class CoachProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years')
    list_filter = ('specialization', 'experience_years')
    search_fields = ('user__email', 'user__username', 'specialization')

class ScoutProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'years_of_experience')
    list_filter = ('organization', 'years_of_experience')
    search_fields = ('user__email', 'user__username', 'organization')

class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    list_filter = ('department',)
    search_fields = ('user__email', 'user__username', 'department')

class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years')
    list_filter = ('specialization', 'experience_years')
    search_fields = ('user__email', 'user__username', 'specialization')

class ClubProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'club_name', 'founded_year', 'league')
    list_filter = ('league',)
    search_fields = ('user__email', 'club_name', 'league')

class FanProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'favorite_club', 'membership_type')
    list_filter = ('membership_type',)
    search_fields = ('user__email', 'user__username', 'favorite_club')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(PlayerProfile, PlayerProfileAdmin)
admin.site.register(CoachProfile, CoachProfileAdmin)
admin.site.register(ScoutProfile, ScoutProfileAdmin)
admin.site.register(ManagerProfile, ManagerProfileAdmin)
admin.site.register(TrainerProfile, TrainerProfileAdmin)
admin.site.register(ClubProfile, ClubProfileAdmin)
admin.site.register(FanProfile, FanProfileAdmin)
