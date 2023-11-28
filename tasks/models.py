from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar
import datetime

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
    
    def get_invites(self):
        """Returns a query set of all the invites this user has received"""

        return self.invite_set.all()

    

class Team(models.Model):
    """Model used to hold teams of different users and their relevant information"""
    
    team_name = models.CharField(max_length=50, unique=True, blank=False)
    team_members = models.ManyToManyField(User, blank=True)
    description = models.TextField(max_length=200, blank=True)
    
    def __str__(self):
        """Overrides string to show the team's name"""
        
        return self.team_name


    def add_creator(self, user):
        """Add the creator of the team to the team"""
        
        # May have administrator rights or something
        self.team_members.add(user)
        self.save()

    def add_team_member(self, new_team_members):
        """Add new team member/s to the team"""
        
        for new_team_member in new_team_members.all():
            self.team_members.add(new_team_member)
            self.save()
        
    def add_invited_member(self, user):
        """Add a new team member from an invite"""

        self.team_members.add(user)
        self.save()
    
    def remove_team_member(self, users_to_remove):
        """Removes user/s from team"""

        # Maybe use a query set for this too
        for user in users_to_remove:
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
    inviting_team = models.ManyToManyField(Team, blank=False)
    invite_message = models.TextField(max_length=100, blank=True)
    status = models.CharField(max_length=30, default="Reject")

    def set_invited_users(self, users):
        """Set the invited users of the invite"""

        for user in users.all():
            self.invited_users.add(user)

    def set_team(self, team):
        """Set the team that will send the invite"""

        self.inviting_team.add(team)
    
    def get_inviting_team(self):
        """Return the inviting team"""

        return self.inviting_team.get(pk=1)

    def close(self, user_to_invite=None):
        """Closes the invite and perform relevant behavior for
        1. invite has been accepted/rejected
        2. If the inviter wants to withdraw the invitation"""

        if self.status == "Accept":
            if user_to_invite:
                self.get_inviting_team().add_invited_member(user_to_invite)   
        elif self.status == "Reject":
            print("Rejected Invite!")
        self.delete()
        
class Task(models.Model):
    """Model used for tasks and information related to them"""

    alphanumeric = RegexValidator(
        r'^[0-9a-zA-Z]{3,}$', 
        'Must have 3 alphanumeric characters!'
        )
    #task_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, blank=False, unique=True, validators=[alphanumeric], primary_key=True)
    description = models.CharField(max_length=530, blank=True)
    due_date = models.DateTimeField(default=datetime.datetime(1, 1, 1))
    created_at = models.DateTimeField(auto_now_add=True)
    # Could add a boolean field to indicate if the task has expired?
