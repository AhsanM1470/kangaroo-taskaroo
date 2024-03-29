"""Forms for the tasks app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import User, Task, Team, Invite, Lane
from django.utils import timezone
from datetime import datetime,timedelta
from datetime import time as tm
from django.core.files.images import get_image_dimensions

class LogInForm(forms.Form):
    """Form enabling registered users to log in."""

    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

    def get_user(self):
        """Returns authenticated user if possible."""

        user = None
        if self.is_valid():
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
        return user


class UserForm(forms.ModelForm):
    """Form to update user profiles."""

    class Meta:
        """Form options."""
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class NewPasswordMixin(forms.Form):
    """Form mixing for new_password and password_confirmation fields."""

    new_password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(),
        validators=[RegexValidator(
            regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).*$',
            message='Password must contain an uppercase character, a lowercase '
                    'character and a number'
            )]
    )
    password_confirmation = forms.CharField(label='Password confirmation', widget=forms.PasswordInput())

    def clean(self):
        """Form mixing for new_password and password_confirmation fields."""

        super().clean()
        new_password = self.cleaned_data.get('new_password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if new_password != password_confirmation:
            self.add_error('password_confirmation', 'Confirmation does not match password.')


class PasswordForm(NewPasswordMixin):
    """Form enabling users to change their password."""

    password = forms.CharField(label='Current password', widget=forms.PasswordInput())

    def __init__(self, user=None, **kwargs):
        """Construct new form instance with a user instance."""
        
        super().__init__(**kwargs)
        self.user = user

    def clean(self):
        """Clean the data and generate messages for any errors."""

        super().clean()
        password = self.cleaned_data.get('password')
        if self.user is not None:
            user = authenticate(username=self.user.username, password=password)
        else:
            user = None
        if user is None:
            self.add_error('password', "Password is invalid")

    def save(self):
        """Save the user's new password."""

        new_password = self.cleaned_data['new_password']
        if self.user is not None:
            self.user.set_password(new_password)
            self.user.save()
        return self.user


class SignUpForm(NewPasswordMixin, forms.ModelForm):
    """Form enabling unregistered users to sign up."""

    class Meta:
        """Form options."""

        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def save(self):
        """Create a new user."""

        super().save(commit=False)
        user = User.objects.create_user(
            self.cleaned_data.get('username'),
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data.get('new_password'),
        )
        return user
    
class TaskForm(forms.ModelForm):
    """Form to input task information"""
    
    class Meta:
        """Form options"""
        
        model = Task
        fields = ["name", "description","dependencies", "priority"]
        widgets = {
            'name' : forms.TextInput(attrs={'class': 'nameClass', 'placeholder': 'Enter the task name...'}),
            'description' : forms.Textarea(attrs={'class': 'descriptionClass', 'placeholder': 'Write a task description...'}),
            # 'lane': forms.Select(attrs={'class':'lane_select'}),
            'priority': forms.Select(attrs={'class': 'priorityClass'}),
        }
        
    """Additional fields"""
    
    dependencies = forms.ModelMultipleChoiceField(queryset = Task.objects.all(),required=False)

    date_field = forms.DateField(
        label='Date',
        widget=forms.SelectDateWidget(),
    )
    time_field = forms.TimeField(
        label='Time',
        widget=forms.TimeInput(attrs={'placeholder': '00:00:00'}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        """Instantiates the possible dependencies the form selection"""
        instance = kwargs.get("instance")
        team = kwargs.get("team")
        
        if team != None:
            kwargs.pop("team")
        
        super(TaskForm, self).__init__(*args, **kwargs)
        
        if instance is None:
            if team is not None:
                self.fields['dependencies'].queryset = Task.objects.filter(assigned_team=team)
        else:
            self.fields['dependencies'].queryset = Task.objects.filter(assigned_team=instance.assigned_team).exclude(id=instance.id)
        
    def clean(self):
        """Cleans the date and time fields within the form and combines them into the datetime field within task"""
        cleaned_data = super().clean()
        date = self.cleaned_data.get('date_field')
        time = self.cleaned_data.get('time_field')
        # Add validation for this:
        if date is not None:
            if time is None:
                time = tm(0,0,0)
            combined_datetime = datetime.combine(date, time)
            if combined_datetime > datetime.now():
                cleaned_data['due_date'] = datetime.combine(date, time)
            else:
                self.add_error("date_field", 'Pick a date-time in the future!')
        return cleaned_data
    
    def save(self, assigned_team_id=None, lane_id=None, commit=True):
        """Create a new task."""
        
        instance = super(TaskForm, self).save(commit=False)
        date = self.cleaned_data.get('date_field')
        time = self.cleaned_data.get('time_field')

        if date is not None:
            if time is None:
                time = tm(0,0,0)
            if datetime.combine(date,time) != instance.due_date:
                instance.deadline_notif_sent = (datetime.today()-timedelta(days=1)).date()
                
            instance.due_date = timezone.make_aware(
                timezone.datetime.combine(date, time),
                timezone.get_current_timezone()
            )
            
        if assigned_team_id is not None:
            instance.assigned_team = Team.objects.get(id=assigned_team_id)
        
        if lane_id is not None:
            instance.lane = Lane.objects.get(id=lane_id)

        instance.priority = self.cleaned_data.get('priority')

        if commit:
            instance.save()
            instance.set_dependencies(self.cleaned_data.get('dependencies'))
            instance.save()
            
        return instance
        
class TaskDeleteForm(forms.Form):
    """Form enabling a user to delete a task."""
    
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'confirmClass'})
    )

class CreateTeamForm(forms.ModelForm):
    """Form enabling a user to create a team."""
    class Meta:
        """Form options."""

        model = Team
        fields = ['team_name', 'description', 'members_to_invite']
        widgets = {
            'team_name' : forms.TextInput(attrs={'placeholder': 'Enter the team name...'}),
            'description' : forms.Textarea(attrs={'placeholder': 'Write a team description...'}),
        }
    
    members_to_invite = forms.CharField(required=False, max_length=300, widget=forms.Select(
                        attrs={
                            'height' : 80,
                            'class': 'basicAutoComplete',
                            'data-url': '/autocomplete_user/',
                            'data-noresults-text': "No users matching query",
                            'autocomplete': 'off'} ))

    def create_team(self, creator):
        """Create a new team, sending the requested members invites to join team"""

        members_to_invite = self.cleaned_data.get("members_to_invite")
        
        team = Team.objects.create(
            team_name=self.cleaned_data.get("team_name"),
            team_creator=creator,
            description=self.cleaned_data.get("description"),
        )

        """Add the creator to team members as well"""
        team.add_invited_member(creator)

        if members_to_invite != "": # If you had members you added in the form
            default_invite = Invite.objects.create(
                invite_message="Please join my team!",
                inviting_team=team)
            default_invite.set_invited_users(members_to_invite)

        return team

class InviteForm(forms.ModelForm):
    """Form enabling a user to create and send an invite to another user"""

    class Meta:
        """Form options."""

        model = Invite
        fields = ['users_to_invite', 'invite_message']
    
    users_to_invite = forms.CharField(required=True, max_length=300, widget=forms.Select(
                    attrs={
                        'height' : 80,
                        'class': 'basicAutoCompleteInvite',
                        'data-url': '/autocomplete_user/',
                        'data-noresults-text': "No users matching query",
                        'autocomplete': 'off'} 
                ))
    
    def send_invite(self, inviting_team=None):
        """Create a new invite and send it to each user"""

        users = self.cleaned_data.get("users_to_invite")

        invite = Invite.objects.create(
            invite_message=self.cleaned_data.get("invite_message"),
            inviting_team=inviting_team,
        )
        invite.set_invited_users(users)

        return invite

class RemoveMemberForm(forms.Form):
    """Form enabling a user to remove a member form a team"""
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'confirmClass'})
    )

class DeleteTeamForm(forms.Form):
    """Form enabling the user to delete a team"""
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'confirmClass'})
    )

class LaneForm(forms.ModelForm):
    """Form enabling a user to create a lane in the dashboard"""

    class Meta:
        model = Lane
        fields = ['lane_name']
    
class LaneDeleteForm(forms.Form):
    """"Form enabling a user to delete a lane in the dashboard"""
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'confirmClass'})
    )

DEMO_CHOICES =( 
    ("1", "Naveen"), 
    ("2", "Pranav"), 
    ("3", "Isha"), 
    ("4", "Saloni"), 
)

class AssignTaskForm(forms.Form):
    """Form enabling a user to assign a task to another user in team"""

    class Meta:
        """Form options."""

        fields = ['team_members']

    team_members = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        """Show all the users who are part of the current team"""

        self.team = kwargs.get("team")
        self.task = kwargs.get("task")

        if self.team != None:
            kwargs.pop("team")
        if self.task != None:
            kwargs.pop("task")

        super().__init__(*args, **kwargs)

        if self.team != None:  
            self.fields["team_members"].queryset = self.team.get_team_members()
        if self.task != None:
            self.fields["team_members"].initial = self.task.assigned_users.all()
    
    def assign_task(self):
        """Assign the task to the team members selected"""

        assigned_users = self.cleaned_data.get("team_members")
        self.task.set_assigned_users(assigned_users)
        self.task.save()
