from typing import Any
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
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

def move_task_left(request, task_name):
    """" Move the task to the left lane """
    if request.method == 'POST':
        task = get_object_or_404(Task, name=task_name)
        current_lane = task.lane
        left_lane = Lane.objects.filter(lane_order__lt=current_lane.lane_order).order_by('-lane_order').first()
        
        if left_lane:
            task.lane = left_lane
            task.save()

        return redirect('dashboard')

def move_task_right(request, task_name):
    """" Move the task to the right lane """
    if request.method == 'POST':
        task = get_object_or_404(Task, name=task_name)
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

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = 'sign_up.html'
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)

class CreateTaskView(LoginRequiredMixin, FormView):
    form_class = TaskForm
    template_name = 'task_create.html'  # Create a template for your task form
    success_url = reverse_lazy('dashboard')  # Redirect to the dashboard after successful form submission
    form_title = 'Create Task'
    
    def form_valid(self, form):
        self.object = form.save()
        #login(self.request, self.object)
        return super().form_valid(form)
    
    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Task created!")
        return reverse_lazy('dashboard')
    
    def post(self, request):
        if request.method == 'POST':
            # Use TaskForm to handle form data, including validation and cleaning
            form = TaskForm(request.POST or None)

            # Check if the form is valid
            if form.is_valid():
                # Save the form data to create a new Task instance
                form.save()
                messages.success(request, 'Task Created!')
                # Redirect to the dashboard or another page
                return redirect('dashboard')
        else:
            form = TaskForm()
        # Fetch all tasks for rendering the form initially
        all_tasks = Task.objects.all()

        return render(request, 'task_create.html', {'tasks': all_tasks, 'form': form})
    
class DeleteTaskView(LoginRequiredMixin, View):
    model = Task
    form_class = TaskDeleteForm
    template_name = 'task_delete.html'  # Create a template for your task form
    success_url = reverse_lazy('dashboard')  # Redirect to the dashboard after successful form submission
    form_title = 'Delete Task'
    context_object_name = 'task'
    
    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Task deleted!")
        return reverse_lazy('dashboard')
    
    def get(self, request, task_name, *args, **kwargs):
        task = get_object_or_404(Task, name=task_name)
        delete_form = TaskDeleteForm()
        # if this doesnt work use domain explicitly
        delete_url = '/task_delete/'+task_name+'/'
        context = {'task': task, 'delete_form': delete_form, 'delete_url': delete_url, 'name': task_name}
        return render(request, self.template_name, context)
    
    def post(self, request, task_name, *args, **kwargs):
        #task_name = kwargs["task_name"]
        task = get_object_or_404(Task, pk=task_name)
        #task = Task.objects.get(pk = task_name)
        if request.method == 'POST':
            delete_form = TaskDeleteForm(request.POST)
            if delete_form.is_valid():
                if delete_form.cleaned_data['confirm_deletion']:
                    task.delete()
                    messages.success(request, 'Task Deleted!')
                    return redirect('dashboard')
        else:
            delete_form = TaskDeleteForm()
        return render(request, 'task_delete.html', {'task':task, 'delete_form': delete_form})
      
def task_search(request):
    q = request.GET.get('q', '')
    data = Task.objects.all()

    if q:
        data = data.filter(name__icontains=q)

    sort_by_due_date = request.GET.get('sort_due_date', None)

    if sort_by_due_date:
        if sort_by_due_date in ['asc', 'desc']:
            order_by = 'due_date' if sort_by_due_date == 'asc' else '-due_date'
            data = data.order_by(order_by)
        else:
            return HttpResponseBadRequest("Invalid value for 'sort_due_date'")

    context = {'data': data}

    # Check if there are no tasks found
    if not data.exists():
        context['no_tasks_found'] = True

    return render(request, 'task_search.html', context)

class DeleteLaneView(LoginRequiredMixin, View):
    """Display form to confirm the deletion of a lane"""
    model = Lane
    form_class = LaneDeleteForm
    template_name = 'lane_delete.html'
    success_url = reverse_lazy('dashboard') 
    form_title = 'Delete Lane'
    context_object_name = 'lane'
    
    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Lane deleted!")
        return reverse_lazy('dashboard')
    
    def get(self, request, lane_id, *args, **kwargs):
        """Return the delete lane URL."""
        lane = get_object_or_404(Lane, lane_id=lane_id)
        delete_form = LaneDeleteForm()
        # if this doesnt work use domain explicitly
        delete_url = '/lane_delete/'+str(lane_id)+'/'
        context = {'lane': lane, 'delete_form': delete_form, 'delete_url': delete_url, 'lane_id': lane_id}
        return render(request, self.template_name, context)
    
    def post(self, request, lane_id, *args, **kwargs):
        """Delete the lane after confirmation."""
        lane = get_object_or_404(Lane, pk=lane_id)
        if request.method == 'POST':
            delete_form = LaneDeleteForm(request.POST)
            if delete_form.is_valid():
                if delete_form.cleaned_data['confirm_deletion']:
                    lane.delete()
                    messages.success(request, 'Lane Deleted!')
                    return redirect('dashboard')
        else:
            delete_form = LaneDeleteForm()
        return render(request, 'lane_delete.html', {'lane':lane, 'delete_form': delete_form})
    
    
class TaskView(LoginRequiredMixin, View):
    model = Task
    form_class = TaskForm
    template_name = 'task_update.html'  # Create a template for your task form
    success_url = reverse_lazy('dashboard')  # Redirect to the dashboard after successful form submission
    
    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Task updated!")
        return reverse_lazy('dashboard')
    
    def get(self, request, task_name, *args, **kwargs):
        task = get_object_or_404(Task, name=task_name)
        form = TaskForm()
        # if this doesnt work use domain explicitly
        update_url = '/task_update/'+task_name+'/'
        context = {'form': form, 'update_url': update_url}
        return render(request, self.template_name, context)
    
    def post(self, request, task_name, *args, **kwargs):
        #task_name = kwargs["task_name"]
        task = get_object_or_404(Task, pk=task_name)
        #task = Task.objects.get(pk = task_name)
        if request.method == 'POST':
            form = TaskForm(request.POST)
            if form.is_valid():
                return redirect('dashboard')
        else:
            delete_form = TaskDeleteForm()
        return render(request, 'task_delete.html', {'task':task, 'delete_form': delete_form})

class InviteView(LoginRequiredMixin, FormView):
    """Functionality for using the invite form"""

    template_name = 'my_teams.html'
    form_class = InviteForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the invite form."""

        kwargs = super().get_form_kwargs(**kwargs)
        print(f"User : {self.request.user}")
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):

        form.send_invite()
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Invite Sent!")
        return reverse('my_teams')