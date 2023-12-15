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
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm, CreateTeamForm, InviteForm, RemoveMemberForm, LaneDeleteForm, DeleteTeamForm
from tasks.helpers import login_prohibited
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from .forms import TaskForm, TaskDeleteForm, AssignTaskForm
from .models import Task, Invite, Team, Lane, Notification, User
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from datetime import datetime
from django.db.models import Max, Case, Value, When

def detect_keydates(team):
    tasks = Task.objects.filter(assigned_team = team)
    print(tasks.count())
    for task in tasks:
        task.notify_keydates()

def formatDateTime(input_date):
    # Parse the input string
    parsed_datetime = datetime.strptime(input_date, '%b. %d, %Y, %I:%M %p')

    # Format the datetime object into 'yyyy-mm-dd hh:mm:ss'
    formatted_datetime = parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')

class DashboardView(LoginRequiredMixin, View):
    """Display dashboard and changes made by the user."""

    template_name = 'dashboard.html'
    success_url = reverse_lazy('dashboard')

    def get(self, request, *args, **kwargs):
        """"Display dashboard data"""
        current_user = request.user
        teams = current_user.get_teams()

        # Get the current team
        if 'dashboard_team' in request.GET:
            team_id = request.GET.get("dashboard_team")
            request.session["current_team_id"] = team_id

        current_team_id = request.session.get("current_team_id", None)
        current_team = Team.objects.filter(id=current_team_id).first() if current_team_id else None

        if current_team is None and teams.exists():
            request.session["current_team_id"] = teams.first().id
            current_team = teams.first()

        self.create_default_lanes(current_team)
        detect_keydates(current_team)

        return render(request, self.template_name, self.get_context_data(current_user, current_team))
    
    # Create 3 default lanes when a new team is made or if all lanes are deleted
    def create_default_lanes(self, current_team):
        default_lane_names = [("Backlog", 1), ("In Progress", 2), ("Complete", 3)]
        if not Lane.objects.filter(team=current_team).exists():
            for lane_name, lane_order in default_lane_names:
                Lane.objects.get_or_create(
                    lane_name=lane_name,
                    lane_order=lane_order,
                    team=current_team
                )

    # Return dashboard data to render
    def get_context_data(self, current_user, current_team):
        if current_team:
            lanes = Lane.objects.filter(team=current_team).order_by('lane_order')
            team_tasks = current_team.get_tasks()
        else:    
            Lane.objects.none()
            Task.objects.none()
        assign_task_form = AssignTaskForm(team=current_team)
        create_task_form = TaskForm(team=current_team)
        invite_form = InviteForm()
        create_team_form = CreateTeamForm()

        return {
            'user': current_user,
            'lanes': lanes,
            'tasks': team_tasks,
            'teams': current_user.get_teams(),
            "current_team": current_team,
            "assign_task_form" : assign_task_form,
            "invite_form" : invite_form,
            "create_task_form": create_task_form,
            "create_team_form": create_team_form,
            'is_dashboard': True
        }
    
    def post(self, request, *args, **kwargs):
        """"Handle user interactions on the dashboard"""

        current_team_id = request.session.get("current_team_id")
        current_team = Team.objects.get(id=current_team_id)

        if 'add_lane' in request.POST:
            self.add_lane(current_team)

        elif 'rename_lane' in request.POST:
            self.rename_lane(request, current_team)

        elif 'move_task_left' in request.POST:
            self.move_task_left(request)
        
        elif 'move_task_right' in request.POST:
            self.move_task_right(request)
        
        elif 'move_lane_left' in request.POST:
            self.move_lane_left(request)
        
        elif 'move_lane_right' in request.POST:
            self.move_lane_right(request)

        return redirect('dashboard')
    
    # Adding a lane to the dashboard
    def add_lane(self, current_team):
        max_order = Lane.objects.filter(team=current_team).aggregate(Max('lane_order'))['lane_order__max'] or 0
        Lane.objects.create(lane_name="New Lane", lane_order=max_order + 1, team=current_team)
    
    # Renaming a lane
    def rename_lane(self, request, current_team):
        lane_id = request.POST.get('rename_lane')
        new_lane_name = request.POST.get('new_lane_name')
        lane = Lane.objects.filter(lane_id=lane_id, team=current_team).first()
        if lane:
            lane.lane_name = new_lane_name
            lane.save()
    
    # Moving a task to the lane on the left
    def move_task_left(self, request):
        task_id = request.POST.get('move_task_left')
        task = get_object_or_404(Task, pk=task_id)
        current_lane = task.lane
        # Filter left lanes within the same team
        left_lane = Lane.objects.filter(lane_order__lt=current_lane.lane_order, team=current_lane.team).order_by('-lane_order').first()
        if left_lane:
            task.lane = left_lane
            task.save()
    
    # Moving a task to the lane on the right
    def move_task_right(self, request):
        task_id = request.POST.get('move_task_right')
        task = get_object_or_404(Task, pk=task_id)
        current_lane = task.lane
        # Filter right lanes within the same team
        right_lane = Lane.objects.filter(lane_order__gt=current_lane.lane_order, team=current_lane.team).order_by('lane_order').first()
        if right_lane:
            task.lane = right_lane
            task.save()
    
    # Moving the lane to the left i.e. putting it 1 lane before in the lane ordering
    def move_lane_left(self, request):
        lane_id = request.POST.get('move_lane_left')
        lane = get_object_or_404(Lane, pk=lane_id)
        previous_lane = Lane.objects.filter(lane_order__lt=lane.lane_order, team=lane.team).order_by('-lane_order').first()

        if previous_lane:
            # temp value to avoid unique value constraint
            temp_order = -1
            lane.lane_order, previous_lane.lane_order = temp_order, lane.lane_order
            lane.save()
            previous_lane.save()
            lane.lane_order = previous_lane.lane_order - 1
            lane.save()
    
    # Moving the lane to the left i.e. putting it 1 lane after in the lane ordering
    def move_lane_right(self, request):
        lane_id = request.POST.get('move_lane_right')
        lane = get_object_or_404(Lane, pk=lane_id)
        next_lane = Lane.objects.filter(lane_order__gt=lane.lane_order, team=lane.team).order_by('lane_order').first()
        if next_lane:
            # temp value to avoid unique value constraint
            temp_order = -1
            lane.lane_order, next_lane.lane_order = temp_order, lane.lane_order
            lane.save()
            next_lane.save()
            lane.lane_order = next_lane.lane_order + 1
            lane.save()

# Autocomplete Query
        
def autocomplete_user(request):
    """Given a query string q, give suggestions for which user it could be"""
    if request.GET.get('q'):
        q = request.GET['q']
        queried_users = q.split(" ")
        new_query = queried_users[-1]

        # Exclude the current user from query
        queried_users.append(request.user.username) 

        # Exclude all members who are already a part of the team
        current_team = Team.objects.get(id=request.session["current_team_id"])
        user_set = User.objects.exclude(id__in=current_team.get_team_members())
        
        # Exclude all users already part of string
        if len(queried_users) > 1:
            data = user_set.exclude(username__in=queried_users).filter(username__icontains=new_query).values_list('username', flat=True)
        else:
            data = user_set.filter(username__icontains=new_query).values_list('username', flat=True)
        
        json = list(data)
        return JsonResponse(json, safe=False)
    else:
        return HttpResponse("Wrong Query")

@login_required
def create_team(request):
    """Form that allows user to create a new team"""

    team = CreateTeamForm()
    if request.method == "POST":
        # Create the team
        current_user = request.user
        team = CreateTeamForm(request.POST)
        if team.is_valid():
            team.create_team(current_user)
            messages.add_message(request, messages.SUCCESS, "Created Team!")
            return redirect("dashboard")
        else:
            messages.add_message(request, messages.ERROR, "That team name has already been taken!")
    
    return render(request, "create_team.html", {"team_form": team})

# @login_required
# def remove_member(request):
#     if request.method == "POST":
#         messages.add_message(request, messages.SUCCESS, "Tried to remove team member, but there ain't no functionality hehe")
#     return redirect("my_teams")


# @login_required
# def assign_task(request, task_id):
#     """Assigns a task to a user using the task model"""

#     print(f"Task = {task_id}")
#     task = Task.objects.get(id=task_id)
#     current_team = Team.objects.filter(id=request.session["current_team_id"]).first()
    
#     if request.method == "GET":
#         assign_task_form = AssignTaskForm(team=current_team, task=task)
#         return render(request, "assign_task.html", {"assign_form": assign_task_form})

#     if request.method == "POST":
#         """Gets the task that has just been pressed"""

#         assign_task_form = AssignTaskForm(request.POST, task=task)
#         if assign_task_form.is_valid():
#             assign_task_form.assign_task()
#             messages.add_message(request, messages.SUCCESS, "Assigned Task!")
#             return redirect("dashboard")
#         else:
#             messages.add_message(request, messages.ERROR, "Task does not exist!")
#             return render(request, "assign_task.html", {"form": assign_task_form})

class AssignTaskView(LoginRequiredMixin, View):
    template_name = 'assign_task.html'  # Create a template for your task form
    success_url = reverse_lazy('dashboard')  # Redirect to the dashboard after successful form submission

    def get(self, request, task_id):
        task = Task.objects.get(id=task_id)
        current_team = Team.objects.get(id=request.session["current_team_id"])
        assign_task_form = AssignTaskForm(team=current_team, task=task)
        return render(request, 'assign_task.html', {'task': task, 'form': assign_task_form})

    def post(self, request, task_id):
        """Post request enabling the user to assign a task to a user"""
        task = Task.objects.get(id=task_id)
        current_team = Team.objects.get(id=request.session["current_team_id"])
        assign_task_form = AssignTaskForm(task=task, data=request.POST)
        if assign_task_form.is_valid():
            assign_task_form.assign_task()
            messages.success(request, 'Assigned Task!')
            return redirect('dashboard')
        else:
            print("frik")
            assign_task_form = AssignTaskForm(team=current_team, task=task)
        return render(request, 'assign_task.html', {'task': task, 'form': assign_task_form})

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

    return redirect("dashboard")

@login_prohibited
def home(request):
    """Display the application's start/home screen."""#

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

    model = User
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
        """Create a new user while automatically creating a default team with the user as its creator"""
        self.object = form.save()
        login(self.request, self.object)
        
        # Create default team
        team = Team.objects.create(
            team_name="My Team",
            team_creator=self.request.user,
            description="A default team for you to start managing your tasks!"
        )
        team = Team.objects.create(
            team_name="My Team",
            team_creator=self.request.user,
            description="A default team for you to start managing your tasks!"
        )
        team.add_invited_member(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)

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
        #! NOT NECESSARY??
        delete_form = LaneDeleteForm()
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

class CreateTaskView(LoginRequiredMixin, FormView):
    """View to handle task creation"""
    form_class = TaskForm
    template_name = 'task_create.html' 
    success_url = reverse_lazy('dashboard')  # Redirect to the dashboard after successful form submission
    form_title = 'Create Task'

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Task created!")
        return reverse_lazy('dashboard')
  
    # def get(self, request):
    #     current_user = request.user
    #     teams = current_user.get_teams()
    #     current_team_id = request.session.get("current_team_id")
    #     current_team = Team.objects.get(id=current_team_id)
    #     if current_team is None and teams.exists():
    #         request.session["current_team_id"] = teams.first().id
    #         current_team = teams.first()
    #     lanes = Lane.objects.filter(team=current_team).order_by('lane_order') if current_team else Lane.objects.none()
    #     #default_lane = Lane.objects.get(name='Backlog')
    #     form = TaskForm(initial={'lane': lanes},team=current_team)
    #     form.fields['lane'].queryset = lanes
    #     all_tasks = Task.objects.all()
    #     return render(request, self.template_name, {'tasks': all_tasks, 'form': form})
    
    def post(self, request):
        """Post request method enabling the user to create a new task"""
        current_user = request.user
        teams = current_user.get_teams()
        if request.method == 'POST':
            # Use TaskForm to handle form data, including validation and cleaning

            # Instantiating lane id
            lane_id = request.POST.get("lane_id")
            if lane_id != "":
                request.session["lane_id"] = request.POST.get("lane_id")

            form = TaskForm(request.POST or None)
            
            # Instantiating current team
            current_team_id = request.session.get("current_team_id")
            current_team = Team.objects.get(id=current_team_id)
            if current_team is None and teams.exists():
                request.session["current_team_id"] = teams.first().id
                current_team = teams.first()
            #lanes = Lane.objects.filter(team=current_team).order_by('lane_order') if current_team else Lane.objects.none()
            lane_id = request.POST.get("lane_id")
            #default_lane = Lane.objects.get(name='Backlog')
            # if form.fields['time_field'] is None:
            #     form.fields['time_field'] = "00:00:00"
            # Check if the form is valid
            if form.is_valid():
                assigned_team_id = request.session["current_team_id"]
                lane_id = request.session["lane_id"]
                form.save(assigned_team_id=assigned_team_id, lane_id=lane_id)
                
                messages.success(request, 'Task Created!')
                # Redirect to the dashboard or another page
                return redirect('dashboard')

        # Fetch all tasks for rendering the form initially
        all_tasks = Task.objects.all()
        return render(request, self.template_name, {'tasks': all_tasks, 'form': form})
    
class DeleteTaskView(LoginRequiredMixin, View):
    """View to handle task deletion"""
    model = Task
    form_class = TaskDeleteForm
    template_name = 'task_delete.html'
    success_url = reverse_lazy('dashboard')  # Redirect to the dashboard after successful form submission
    form_title = 'Delete Task'
    context_object_name = 'task'
    
    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Task deleted!")
        return reverse_lazy('dashboard')
    
    def get(self, request,pk, *args, **kwargs):
        """Get request method to load the deletion form for a given task"""
        task = get_object_or_404(Task, pk=pk)
        delete_form = TaskDeleteForm()
        delete_url = reverse('task_delete', kwargs={'pk': pk})
        context = {'task': task, 'delete_form': delete_form, 'delete_url': delete_url, 'name': task.name}
        return render(request, self.template_name, context)
    
    def post(self, request, pk, *args, **kwargs):
        """Post request method to handle task deletion form submission"""
        task = get_object_or_404(Task, pk=pk)
        if request.method == 'POST':
            delete_form = TaskDeleteForm(request.POST)
            
            # Check if the form is valid
            if delete_form.is_valid():
                if delete_form.cleaned_data['confirm_deletion']:
                    task.delete()
                    messages.success(request, 'Task Deleted!')
                    return redirect('dashboard')
        else:
            delete_form = TaskDeleteForm()
        return render(request, 'task_delete.html', {'task':task, 'delete_form': delete_form})
    
class TaskEditView(LoginRequiredMixin, View):
    """View to handle task modification"""
    model = Task
    form_class = TaskForm
    template_name = 'task_edit.html' 
    success_url = reverse_lazy('dashboard')  # Redirect to the dashboard after successful form submission
    
    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Task updated!")
        return reverse_lazy('dashboard')
    
    def get(self, request, pk, *args, **kwargs):
        """Get request method to load the task edit form for a given task"""
        task = get_object_or_404(Task, pk=pk)
        date_field = task.due_date.date()
        time_field = task.due_date.time()
        initial_data = {
            'name' : task.name,
            'description' : task.description,
            'date_field' : date_field,
            'time_field' : time_field
        }
        # Passing in the task to be modified into the form
        form = TaskForm(initial=initial_data, instance=task)
        update_url = reverse('task_edit', kwargs={'pk': pk})
        context = {'form': form, 'update_url': update_url, 'task': task}
        return render(request, self.template_name, context)
    
    def post(self, request, pk, *args, **kwargs):
        """Post request method to handle task edit form submissions"""
        task = get_object_or_404(Task, pk=pk)
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task Updated!')
            return redirect('dashboard')
        return render(request, 'task_edit.html', {'task':task, 'form': form})
    
class TaskView(LoginRequiredMixin, View):
    """View to handle task info requests"""
    model = Task
    template_name = 'task.html' 
    
    def get_success_url(self):
        """Return redirect URL after successful update."""
        return reverse_lazy('dashboard')
    
    def get(self, request, pk, *args, **kwargs):
        """Get request method to return information about a given task"""
        task = get_object_or_404(Task, pk=pk)
        context = {'task': task}
        return render(request, self.template_name, context)
    
priority_order = Case(
    When(priority='high', then=Value(3)),
    When(priority='medium', then=Value(2)),
    When(priority='low', then=Value(1))
)

def task_search(request):
    
    q = request.GET.get('q', '')
    data = Task.objects.all()
    # If a search query is provided, filter tasks based on the 'name' field containing the query string.
    if q:
        data = data.filter(name__icontains=q)

    sort_column = request.GET.get('sort_column', None)
    sort_direction = request.GET.get('sort_direction', None)
    if sort_column == 'priority':
        data=data.model.objects.alias(priority_order=priority_order)
        sort_column = 'priority_order'
    if sort_column:
        # Sort in descending order if 'desc' is specified.
        if sort_direction == 'desc':
          data = data.order_by('-'+sort_column)
        else:
          # Default is ascending order
          data = data.order_by(sort_column)

    context = {'data': data}
    if not data.exists():
        context['no_tasks_found'] = True

    return render(request, 'task_search.html', context)

def notif_delete(request,notif_id):
    notification = Notification.objects.get(pk=notif_id)
    notification.delete()
    return redirect('dashboard')

class InviteView(LoginRequiredMixin, FormView):
    """Functionality for using the invite form"""

    template_name = 'invite.html'
    form_class = InviteForm

    # def get_form_kwargs(self, **kwargs):
    #     """Pass the current user to the invite form."""

    #     kwargs = super().get_form_kwargs(**kwargs)
    #     kwargs.update({'user': self.request.user})
    #     return kwargs

    def form_valid(self, form):
        
        inviting_team = Team.objects.get(id=self.request.session["current_team_id"])
        form.send_invite(inviting_team=inviting_team)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Invite Sent!")
        return reverse('dashboard')

class DeleteTeamView(LoginRequiredMixin, FormView):
    model = Team
    form_class = DeleteTeamForm
    template_name = 'delete_team.html' 
    form_title = 'Delete Team'
    
    def post(self, request, team_id):
        """Get the team, and render the team delete form"""
        team = get_object_or_404(Team, id=team_id)
        user = request.user
        if (len(user.get_teams()) > 1): 
            delete_form = DeleteTeamForm(request.POST)
            if delete_form.is_valid():
                if delete_form.cleaned_data['confirm_deletion']:
                    team.delete()
                    messages.success(request, 'Team Deleted!')
                    return redirect('dashboard')
        else:
            messages.error(request, 'Cannot have 0 teams!')
            return redirect("dashboard")
            
        return render(request, "delete_team.html", {'team':team, 'delete_form': delete_form})
    
class RemoveMemberView(LoginRequiredMixin, FormView):
    form_class = RemoveMemberForm
    template_name = 'remove_team_member.html' 
    form_title = 'Remove Team Member'

    def post(self, request, member_id):
        """Get the team, and remove the requested team member"""

        if "team_id" in request.POST:
            request.session["team_id"] = request.POST.get("current_team_id")

        team = get_object_or_404(Team, id=request.session["current_team_id"])
        user = User.objects.get(id=member_id)

        remove_member_form = RemoveMemberForm(request.POST)
        if remove_member_form.is_valid():
            if remove_member_form.cleaned_data['confirm_deletion']:
                team.remove_team_member(user)
                messages.success(request, f'{user.username} has been removed from {team.team_name}!')
                return redirect('dashboard')
        else:
            remove_member_form = RemoveMemberForm()
            
        return render(request, "remove_team_member.html", {'user':user, 'team':team, 'remove_member_form': remove_member_form})
    