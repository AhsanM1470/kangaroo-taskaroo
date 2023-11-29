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
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm, CreateTeamForm, InviteForm
from tasks.helpers import login_prohibited
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from .forms import TaskForm, TaskDeleteForm
from .models import Task, Invite
from datetime import datetime

@login_required
def dashboard(request):
    """Display and modify the current user's dashboard."""

    # Initialize lanes in the session if they don't exist
    if 'lanes' not in request.session:
        request.session['lanes'] = ['Backlog', 'In Progress', 'Complete']

    # Handle form submission for adding a new lane
    if request.method == 'POST':
        if 'add_lane' in request.POST:
            new_lane_name = 'New Lane'  # Or dynamically generate the name
            request.session['lanes'].append(new_lane_name)
            request.session.modified = True  # Mark session as modified to save it

        elif 'delete_lane' in request.POST:
                lane_to_delete = request.POST.get('delete_lane')
                if lane_to_delete in request.session['lanes']:
                    request.session['lanes'].remove(lane_to_delete)
                    request.session.modified = True

        elif 'rename_lane' in request.POST:
            new_lane_name = request.POST.get('new_lane_name')
            lane_index = int(request.POST.get('lane_index'))
            if 0 <= lane_index < len(request.session['lanes']):
                request.session['lanes'][lane_index] = new_lane_name
                request.session.modified = True

        return redirect('dashboard')  # Redirect to the same page to show the updated lanes

    # Retrieve current user and lanes
    current_user = request.user
    lanes = request.session['lanes']
    return render(request, 'dashboard.html', {'user': current_user, 'lanes': lanes})

# def dashboard(request):
#     """Display and modify the current user's dashboard."""
#     print("Dashboard accessed.")

#     if 'lanes' not in request.session:
#         request.session['lanes'] = [{'id': 1, 'name': 'Backlog'},
#                                     {'id': 2, 'name': 'In Progress'},
#                                     {'id': 3, 'name': 'Complete'}]
#     print(request.session.get('lanes'))

#     if request.method == 'POST':
#         if 'add_lane' in request.POST:
#             new_id = max((lane['id'] for lane in request.session.get('lanes')), default=0) + 1
#             new_lane = {'id': new_id, 'name': 'New Lane'}
#             request.session['lanes'].append(new_lane)
#             request.session.modified = True

#         elif 'delete_lane' in request.POST:
#             lane_to_delete = request.POST.get('delete_lane')
#             print(request.session.get('lanes'))
#             request.session['lanes'] = [lane for lane in request.session.get('lanes') if lane['name'] != lane_to_delete]
#             request.session.modified = True

#         elif 'edit_lane' in request.POST:
#             lane_id = int(request.POST.get('lane_id'))
#             new_lane_name = request.POST.get('new_lane_name')
#             for lane in request.session.get('lanes'):
#                 if lane['id'] == lane_id:
#                     lane['name'] = new_lane_name
#                     break
#             request.session.modified = True

#         return redirect('dashboard')

#     current_user = request.user
#     lanes = request.session.get('lanes')
#     return render(request, 'dashboard.html', {'user': current_user, 'lanes': lanes})

@login_required
def create_team(request):
    """Form that allows user to create a new team"""
    if request.method == "POST":
        # Create the team
        current_user = request.user
        team = CreateTeamForm(request.POST)
        if team.is_valid():
            team.create_team(user=current_user)
        else:
            messages.add_message(request, messages.ERROR, "That team name has already been taken!")
    return redirect("my_teams")

@login_required
def my_teams(request):
    """Display the user's teams page and their invites"""

    current_user = request.user
    user_teams = current_user.get_teams()
    user_invites = current_user.get_invites()
    team_form = CreateTeamForm()
    invite_form = InviteForm()
    return render(request, 'my_teams.html', {'teams': user_teams, 'invites': user_invites, 'team_form': team_form, "invite_form" : invite_form})

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

class TaskView(LoginRequiredMixin, FormView):
   
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
                name = form.cleaned_data['name']
                description = form.cleaned_data['description']
                #date_field
                due_date = form.cleaned_data['due_date']
            
                model = Task.objects.create(
                    name=name,
                    description=description,
                    due_date=due_date
                )
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
        context = {'task': task, 'delete_form': delete_form}
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
        
    
class InviteView(LoginRequiredMixin, FormView):
    """Display invite form"""

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


