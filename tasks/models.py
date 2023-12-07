from typing import Any
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.views.generic import DeleteView
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm, CreateTeamForm, InviteForm, RemoveMemberForm, LaneDeleteForm
from tasks.helpers import login_prohibited
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from .forms import TaskForm, TaskDeleteForm
from .models import Task, Invite, Team, Lane
from django.http import HttpResponseBadRequest
from datetime import datetime
from django.db.models import Max


@login_required

def dashboard(request):
    """Display and modify the current user's dashboard."""

    # Initialize lanes in the session if they don't exist
    if request.method == 'GET':
        if not Lane.objects.exists():
            default_lane_names = [("Backlog", 1), ("In Progress", 2), ("Complete", 3)]
            for lane_name, lane_order in default_lane_names:
                Lane.objects.get_or_create(lane_name=lane_name, lane_order=lane_order)
    
    
    if request.method == 'GET':
        # Create 3 default lanes when the dashboard is empty
        if not Lane.objects.exists():
            default_lanes = ['Backlog', 'In Progress', 'Complete']
            for lane_name in default_lanes:
                Lane.objects.get_or_create(lane_name = lane_name)
    
    if request.method == 'POST':
        # Add a lane to the dashboard
        if 'add_lane' in request.POST:
            max_order = Lane.objects.aggregate(Max('lane_order'))['lane_order__max'] or 0
            Lane.objects.create(lane_name="New Lane", lane_order=max_order + 1)

        # Rename the dashboard lane
        elif 'rename_lane' in request.POST:
            lane_id = request.POST.get('rename_lane')
            new_lane_name = request.POST.get('new_lane_name')
            # if lane_id and new_lane_name:
            lane = Lane.objects.get(lane_id=lane_id)
            lane.lane_name = new_lane_name
            lane.save()
        
        return redirect('dashboard')

    # Retrieve current user, lanes, tasks, and the teams
    current_user = request.user
    # lanes = request.session['lanes']
    lanes = lanes = Lane.objects.all().order_by('lane_order')
    all_tasks = Task.objects.all()
    # Used to be all teams
    teams = current_user.get_teams()
    task_form = TaskForm()
    return render(request, 'dashboard.html', {
        'user': current_user,
        'lanes': lanes,
        'tasks': all_tasks,
        'teams': teams,
        'task_form': task_form,
    })

def move_task_left(request, pk):
    """" Move the task to the left lane """
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk)
        current_lane = task.lane
        left_lane = Lane.objects.filter(lane_order__lt=current_lane.lane_order).order_by('-lane_order').first()
        
        if left_lane:
            task.lane = left_lane
            task.save()

        return redirect('dashboard')

def move_task_right(request, pk):
    """" Move the task to the right lane """
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk)
        current_lane = task.lane
        right_lane = Lane.objects.filter(lane_order__gt=current_lane.lane_order).order_by('lane_order').first()
        
        if right_lane:
            task.lane = right_lane
            task.save()

        return redirect('dashboard')
    
def move_lane_left(request, lane_id):
    """" Move the lane 1 space left """
    if request.method == 'POST':
        lane = get_object_or_404(Lane, pk=lane_id)
        # Swap order with the previous lane if it exists
        previous_lane = Lane.objects.filter(lane_order__lt=lane.lane_order).order_by('-lane_order').first()
        if previous_lane:
            lane.lane_order, previous_lane.lane_order = previous_lane.lane_order, lane.lane_order
            lane.save()
            previous_lane.save()
        return redirect('dashboard')

def move_lane_right(request, lane_id):
    """" Move the lane 1 space right """
    if request.method == 'POST':
        lane = get_object_or_404(Lane, pk=lane_id)
        # Swap order with the next lane if it exists
        next_lane = Lane.objects.filter(lane_order__gt=lane.lane_order).order_by('lane_order').first()
        if next_lane:
            lane.lane_order, next_lane.lane_order = next_lane.lane_order, lane.lane_order
            lane.save()
            next_lane.save()
        return redirect('dashboard')

@login_required
def create_team(request):
    """Form that allows user to create a new team"""
    if request.method == "POST":
        # Create the team
        current_user = request.user
        team = CreateTeamForm(request.POST)
        if team.is_valid():
            team.create_team(current_user)
            messages.add_message(request, messages.SUCCESS, "Created Team!")
        else:
            messages.add_message(request, messages.ERROR, "That team name has already been taken!")
    return redirect("my_teams")

@login_required
def my_teams(request):
    """Display the user's teams page and their invites"""

    current_user = request.user
    user_teams = current_user.get_teams()
    user_invites = current_user.get_invites()
    team_form = CreateTeamForm(user=current_user)

    """Only show the invite and remove form for creators of teams"""
    if len(current_user.get_created_teams()) > 0:
        invite_form = InviteForm(user=current_user)
        remove_form = RemoveMemberForm()
        return render(request, 'my_teams.html', {'teams': user_teams, 'invites': user_invites, 
                                                 'team_form': team_form, "invite_form" : invite_form,
                                                 "remove_form": remove_form})
    else:
        return render(request, 'my_teams.html', 
                      {'teams': user_teams, 'invites': user_invites, 
                       'team_form': team_form})

@login_required
def remove_member(request):
    if request.method == "POST":
        messages.add_message(request, messages.SUCCESS, "Tried to remove team member, but there ain't no functionality hehe")
    return redirect("my_teams")


@login_required
def press_invite(request):
    """Functionality for the accept/reject buttons of invite"""
    
    if request.method == "POST":
        invite = Invite.objects.get(id=request.POST.get('id'))
        user = request.user

        if request.POST.get('status'):
            invite.status = request.POST.get('status')
            invite.close(user)
        else:
            messages.add_message(request, messages.ERROR, "A choice wasn't made!")

    return redirect("my_teams")

@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')


class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url


class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

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
    # Could add a boolean field to indicate if the task has expired?

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
