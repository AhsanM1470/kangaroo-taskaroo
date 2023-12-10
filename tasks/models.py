from collections.abc import Collection
from django.core.validators import RegexValidator, MaxLengthValidator
from django.core.exceptions import ValidationError 
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar
from datetime import datetime, timezone, timedelta
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
    notifications = models.ManyToManyField('Notification')

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

    def get_tasks(self):
        """Returns a query set of all the tasks this user has been assigned"""

        return self.task_set.all()

    def add_notification(self,notif):
        """Adds a notification to the user's list of notifications"""
        self.notifications.add(notif)
        self.save()

    def get_notifications(self):
        """Returns a query set of the user's notifications"""
        return self.notifications.all()

    

class Team(models.Model):
    """Model used to hold teams of different users and their relevant information"""
    
    
    team_name = models.CharField(max_length=50, blank=False)
    team_creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, related_name="created_teams")
    team_members = models.ManyToManyField(User, blank=True)
    description = models.TextField(blank=True, validators=[MaxLengthValidator(200)])
    
    def __str__(self):
        """Overrides string to show the team's name"""
        
        return self.team_name
        
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

    def get_tasks(self):
        """Return query set containing all the tasks of the team"""

        return self.task_set.all()

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
            notif = InviteNotification.objects.create(invite=self)
            user.add_notification(notif)

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
                self.invited_users.remove(user_to_invite)  
                notifs = user_to_invite.get_notifications()
                notif = list(filter(lambda notif: notif.as_invite_notif() != None and notif.as_invite_notif().invite == self,notifs))[0]
                notif.delete()
                self.save()
        if self.invited_users.count()==0:
            self.delete()
    
class Lane(models.Model):
    """Model used for lanes and information related to them"""
    alphanumeric = RegexValidator(
        regex=r'^[a-zA-Z0-9 ]{1,}$',
        message='Enter a valid word with at least 1 alphanumeric character (no special characters allowed).',
        code='invalid_lane_name'
    )

    lane_name = models.CharField(max_length=50, blank=False, validators=[alphanumeric])
    lane_id = models.AutoField(primary_key=True)
    lane_order = models.IntegerField(default=0, unique=True, blank=False)

    class Meta:
        ordering = ['lane_order']

    def __str__(self):
        return self.lane_name
        
class Task(models.Model):
    """Model used for tasks and information related to them"""
    #taskID = models.AutoField(primary_key=True, unique=True)
    alphanumeric = RegexValidator(
        regex=r'^[a-zA-Z0-9 ]{3,}$',
        message='Enter a valid word with at least 3 alphanumeric characters (no special characters allowed).',
        code='invalid_word',
    )
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium',
    )
    #task_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, blank=False, unique=True, validators=[alphanumeric], primary_key=False)
    description = models.CharField(max_length=530, blank=True)
    due_date = models.DateTimeField(default=datetime(1, 1, 1))
    created_at = models.DateTimeField(default=timezone.now)
    lane = models.ForeignKey(Lane, on_delete=models.CASCADE)
    assigned_team = models.ForeignKey(Team, blank=False, on_delete=models.CASCADE, null=True)
    assigned_users = models.ManyToManyField(User, blank=True)
    deadline_notif_sent = models.BooleanField(default=False)

    def get_assigned_users(self):
        """Return all users assigned to this task"""

        return self.assigned_users.all()

    def set_assigned_users(self, assigned_users):
        """Set the assigned users of the task"""

        for user in assigned_users:
            self.assigned_users.add(user)
            self.save()
            notif = TaskNotification.objects.create(task=self,notification_type="AS")
            user.add_notification(notif)

    def notify_keydates(self):
        if datetime.today().date() >= (self.due_date-timedelta(days=5)).date() and not self.deadline_notif_sent:
            self.deadline_notif_sent=True
            notif = TaskNotification.objects.create(task=self,notification_type="DL")
            for user in self.assigned_team.team_members.all():
                user.add_notification(notif)
        self.save()


    # Could add a boolean field to indicate if the task has expired?

"""
class AssignedTask(models.Model):
    #M odel used for holding the information about a task assigned to a specific user of a team
    assigned_member = models.ForeignKey(User, blank=True, on_delete=models.CASCADE, default=None)
    team = models.ForeignKey(Team, blank=False, on_delete=models.CASCADE)
    task = models.OneToOneField(Task, blank=False, on_delete=models.CASCADE)

    def add_assigned_members(self, assigned_members):
        #Set assigned team member/s to task
        
        for team_member in assigned_members.all():
            self.assigned_members.add(team_member)
            self.save()

"""


class Notification(models.Model): 
    """Generic template model for notifications"""
    def as_task_notif(self):
        try:
            return self.tasknotification
        except TaskNotification.DoesNotExist:
            return None

    def as_invite_notif(self):
        try:
            return self.invitenotification
        except InviteNotification.DoesNotExist:
            return None

    def display(self):
        return "This is a notification"

class TaskNotification(Notification): 
    """Model used to represent a notification relating to a specific task"""

    class NotificationType(models.TextChoices):
        ASSIGNMENT = "AS"
        DEADLINE = "DL"

    task = models.ForeignKey(Task,blank=False,on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=2,choices=NotificationType.choices,default=NotificationType.ASSIGNMENT)

    def set_type(new_type):
        notification_type = new_type

    def display(self):
        if self.notification_type== self.NotificationType.ASSIGNMENT:
            return f'{self.task.name} has been assigned to you.'
        elif self.notification_type == self.NotificationType.DEADLINE:
            if datetime.today().date()<self.task.due_date.date():
                return f"{self.task.name}'s deadline is in {(self.task.due_date.date()-datetime.today().date()).days} day(s)."
            else:
                return f"{self.task.name}'s deadline has passed."

class InviteNotification(Notification): 
    """Model used to represent a notification relating to a team invite"""
    invite = models.ForeignKey(Invite,blank=False,on_delete=models.CASCADE)

    def display(self):
       return f"Do you wish to join {self.invite.get_inviting_team().team_name}?"