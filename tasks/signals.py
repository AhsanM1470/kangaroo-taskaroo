from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Team


# When a new user is made, this checks if the user is a super user and then creates a default team for them
@receiver(post_save, sender=get_user_model())
def create_team_for_superuser(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        # Create a team for the superuser
        if instance.get_teams().count ==0:
            
            team = Team.objects.create(
                team_name="My Team",
                team_creator=instance
                )
            team.add_invited_member(instance)
        
        
# When a normal user is turned into a super user, if the user does not have any teams it will create a defaut team for them
@receiver(post_save, sender=get_user_model())
def create_team_for_superuser(sender, instance, **kwargs):
    # Check if the user is now a superuser
    if instance.is_superuser:
        # Check if the user already has a team
        if instance.get_teams().count() == 0:
            # Create a team for the superuser
            team = Team.objects.create(
                team_name="My Team",
                team_creator=instance
            )
            team.add_invited_member(instance)
            
