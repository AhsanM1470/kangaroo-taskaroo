from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar

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
    team_members = models.ManyToManyField(User)
    description = models.TextField(max_length=200, blank=True)
        
    def add_team_member(self, newUser):
        """Add a new user to the users field"""
        
        self.team_members.add(newUser)
        self.save()
    
    def remove_team_member(self, user_to_remove):
        """Removes user from team"""

        self.team_members.remove(user_to_remove)
        self.save()
    
    def get_team_members(self):
        """Returns query set containing all the users in team"""

        return self.team_members.all()

class Invite(models.Model):
    """Model used to hold information about invites"""
    invited_users = models.ManyToManyField(User)
    inviting_team = models.ManyToManyField(Team)
    invite_message = models.TextField(max_length=100, blank=True)

    def __str__(self):
        """Prints out the invite in nice formatting"""
        return ""
    
    def send_invite(self):
        for user in self.invited_users:
            user.invite_set.add(self)

    def delete_invite(self):
        """Delete invite because 1. Invite has been completed, or 2. The inviter wants to undo the invitation"""
        #team = Team.objects.get(team_name=self.inviting_team_name)
        self.delete()

        

