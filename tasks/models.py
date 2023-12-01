from collections.abc import Collection
from django.core.validators import RegexValidator, MaxLengthValidator
from django.core.exceptions import ValidationError 
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar
from datetime import datetime, timezone
from django.utils import timezone

class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(
            regex=r'^@\w{3,}$',
            message='Username must consist of @ followed by at least three alphanumericals'
        )]
    )
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)

    class Meta:
        """Model options."""

        ordering = ['last_name', 'first_name']

    def full_name(self):
        """Return a string containing the user's full name."""

        return f'{self.first_name} {self.last_name}'

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""

        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default='mp')
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""
        
        return self.gravatar(size=60)

    def get_teams(self):
        """Returns a query set of set of teams this user is a part of"""

        return self.team_set.all()
    
    def get_created_teams(self):
        """Returns a query set of all the teams this user has created"""

        return self.created_teams.all()
    
    def get_invites(self):
        """Returns a query set of all the invites this user has received"""

        return self.invite_set.all()

    

class Team(models.Model):
    """Model used to hold teams of different users and their relevant information"""
    
    team_name = models.CharField(max_length=50, unique=True, blank=False)
    team_creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, related_name="created_teams")
    team_members = models.ManyToManyField(User, blank=True)
    description = models.TextField(blank=True, validators=[MaxLengthValidator(200)])
    
    def __str__(self):
        """Overrides string to show the team's name"""
        
        return self.team_name

    def add_team_member(self, new_team_members):
        """Add new team member/s to the team"""
        
        for new_team_member in new_team_members.all():
            self.team_members.add(new_team_member)
            self.save()
        
    def add_invited_member(self, user):
        """Add a new team member from an invite"""

        self.team_members.add(user)
        self.save()
    
    def remove_team_member(self, user):
        """Removes user from team"""

        if user == self.team_creator:
            print("Cannot remove the team's creator!")
        
        else:
            self.team_members.remove(user)
            self.save()
    
    def get_team_members(self):
        """Returns query set containing all the users in team"""

        return self.team_members.all()

    def get_team_members_list(self):
        """Return a string which shows the list of all the users in team"""

        output_str = ""
        users = self.get_team_members()

        for user in users:
            output_str += f'{user.username} '
        return output_str

class Invite(models.Model):
    """Model used to hold information about invites"""
    invited_users = models.ManyToManyField(User, blank=False)
    inviting_team = models.ForeignKey(Team, on_delete=models.CASCADE, default=None, blank=False)
    invite_message = models.TextField(validators=[MaxLengthValidator(100)], blank=True)
    status = models.CharField(max_length=30, default="Reject")

    def clean(self):
        super().clean()

    def set_invited_users(self, users):
        """Set the invited users of the invite"""

        for user in users.all():
            self.invited_users.add(user)
            self.save()

    def set_team(self, team):
        """Set the team that will send the invite"""
        
        print(team)
        self.inviting_team = team
        self.save()

    def get_inviting_team(self):
        """Return the inviting team"""

        return self.inviting_team

    def close(self, user_to_invite=None):
        """Closes the invite and perform relevant behavior for
        1. invite has been accepted/rejected
        2. If the inviter wants to withdraw the invitation"""

        if self.status == "Accept":
            if user_to_invite:
                self.get_inviting_team().add_invited_member(user_to_invite)   
        self.delete()
    
class Lane(models.Model):
    lane_name = models.CharField(max_length=100)
    lane_id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.lane_name
        
class Task(models.Model):
    """Model used for tasks and information related to them"""
    #taskID = models.AutoField(primary_key=True, unique=True)
    alphanumeric = RegexValidator(
        r'^[0-9a-zA-Z]{3,}$', 
        'Must have 3 alphanumeric characters!'
        )
    #task_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, blank=False, unique=True, validators=[alphanumeric], primary_key=True)
    description = models.CharField(max_length=530, blank=True)
    due_date = models.DateTimeField(default=datetime(1, 1, 1))
    created_at = models.DateTimeField(default=timezone.now)
    #lane = models.ForeignKey(Lane, on_delete=models.CASCADE)
    # Could add a boolean field to indicate if the task has expired?
    lane = models.ForeignKey(Lane, on_delete=models.CASCADE, related_name='tasks', default=Lane.objects.first())

class Notification(models.Model): 
    """Model used to represent a notification"""

    class NotificationType(models.TextChoices):
        ASSIGNMENT = "AS"
        DEADLINE = "DL"

    task_name = models.CharField(max_length=50)

    def display(self,notification_type):
        if notification_type== self.NotificationType.ASSIGNMENT:
            return f'{self.task_name} has been assigned to you.'
        elif notification_type == self.NotificationType.DEADLINE:
            return f"{self.task_name}'s deadline is approaching."