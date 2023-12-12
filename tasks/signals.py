from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from tasks.models import Profile

@receiver(post_save, sender=User)
def create_or_save_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Ensure that the profile exists to avoid recursive save
        profile, created = Profile.objects.get_or_create(user=instance)
        profile.save()
