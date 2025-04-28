from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    CustomUser, PlayerProfile, CoachProfile, ScoutProfile,
    ManagerProfile, TrainerProfile, ClubProfile, FanProfile
)

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == CustomUser.Role.PLAYER:
            PlayerProfile.objects.create(user=instance)
        elif instance.role == CustomUser.Role.COACH:
            CoachProfile.objects.create(user=instance)
        elif instance.role == CustomUser.Role.SCOUT:
            ScoutProfile.objects.create(user=instance)
        elif instance.role == CustomUser.Role.MANAGER:
            ManagerProfile.objects.create(user=instance)
        elif instance.role == CustomUser.Role.TRAINER:
            TrainerProfile.objects.create(user=instance)
        elif instance.role == CustomUser.Role.CLUB:
            ClubProfile.objects.create(user=instance)
        elif instance.role == CustomUser.Role.FAN:
            FanProfile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.role == CustomUser.Role.PLAYER:
        if hasattr(instance, 'player_profile'):
            instance.player_profile.save()
    elif instance.role == CustomUser.Role.COACH:
        if hasattr(instance, 'coach_profile'):
            instance.coach_profile.save()
    elif instance.role == CustomUser.Role.SCOUT:
        if hasattr(instance, 'scout_profile'):
            instance.scout_profile.save()
    elif instance.role == CustomUser.Role.MANAGER:
        if hasattr(instance, 'manager_profile'):
            instance.manager_profile.save()
    elif instance.role == CustomUser.Role.TRAINER:
        if hasattr(instance, 'trainer_profile'):
            instance.trainer_profile.save()
    elif instance.role == CustomUser.Role.CLUB:
        if hasattr(instance, 'club_profile'):
            instance.club_profile.save()
    elif instance.role == CustomUser.Role.FAN:
        if hasattr(instance, 'fan_profile'):
            instance.fan_profile.save() 