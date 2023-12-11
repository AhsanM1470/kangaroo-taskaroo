"""Forms for the tasks app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import User, Task, Team, Invite, Lane
from django.utils import timezone
from datetime import datetime,timedelta


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
        fields = ["name", "description", "lane", "priority"]
        widgets = {
            'name' : forms.TextInput(attrs={'class': 'nameClass', 'placeholder': 'Enter the team name...'}),
            'description' : forms.Textarea(attrs={'class': 'descriptionClass', 'placeholder': 'Write a team description...'}),
            'lane': forms.Select(attrs={'class':'lane_select'}),
            'priority': forms.Select(attrs={'class': 'priorityClass'}),
        }
    #
    # priority = forms.ChoiceField(
    #     choices=Task.PRIORITY_CHOICES,
    #     widget=forms.Select(attrs={'class': 'priorityClass'}),
    # )
     
    date_field = forms.DateField(
        label='Date',
        widget=forms.SelectDateWidget(),
    )
    time_field = forms.TimeField(
        label='Time',
        widget=forms.TimeInput(attrs={'placeholder': '00:00:00'}),
    )

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['lane'].queryset = Lane.objects.all()
        
        # self.fields['lane'].initial = Lane.objects.first()
        
    def clean(self):
        cleaned_data = super().clean()
        date = self.cleaned_data.get('date_field')
        time = self.cleaned_data.get('time_field')
        # Add validation for this:
        if date is not None and time is not None:
            combined_datetime = datetime.combine(date, time)
            if combined_datetime > datetime.now():
                cleaned_data['due_date'] = datetime.combine(date, time)
            else:
                # Simon Stuff!
                self.add_error("date_field", 'Pick a date-time in the future!')
                #raise ValidationError('Pick a date-time in the future!')
        return cleaned_data
    
    def save(self, assigned_team_id=None, commit=True):
        instance = super(TaskForm, self).save(commit=False)
        date = self.cleaned_data.get('date_field')
        time = self.cleaned_data.get('time_field')

        if date is not None and time is not None:
            if datetime.combine(date,time) != instance.due_date:
                instance.deadline_notif_sent = (datetime.today()-timedelta(days=1)).date()
            instance.due_date = datetime.combine(date, time)
            
        if assigned_team_id is not None:
            instance.assigned_team = Team.objects.get(id=assigned_team_id)

        instance.priority = self.cleaned_data.get('priority')

        if commit:
            instance.save()
            
        return instance
        
class TaskDeleteForm(forms.Form):
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'confirmClass'})
    )

class CreateTeamForm(forms.ModelForm):
    """Form enabling a user to create a team"""

    class Meta:
        """Form options."""

        model = Team
        fields = ['team_name', 'description', 'members_to_invite']
        widgets = {
            'team_name' : forms.TextInput(attrs={'placeholder': 'Enter the task name...'}),
            'description' : forms.Textarea(attrs={'placeholder': 'Write a task description...'}),
        }

    members_to_invite = forms.ModelMultipleChoiceField(User.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        """Makes sure the creator of team is not shown as option to add"""

        self.creator = kwargs.get("user")
        if self.creator != None:
            kwargs.pop("user") 

        super().__init__(*args, **kwargs)

        if self.creator != None:
            self.fields["members_to_invite"].queryset = User.objects.exclude(username=self.creator.username)
    
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

        if members_to_invite != None: # If you had members you added in the form
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
        fields = ['invited_users', 'invite_message', "team_to_join"]
    
    team_to_join = forms.ModelChoiceField(queryset=Team.objects.all(), required=True)
    
    def __init__(self, user=None, **kwargs):
        """Makes sure only teams that the current user belongs to are given as options"""
        """Makes sure only users who are not already part of the team are shown"""

        self.user = user
        super().__init__(**kwargs)

        if self.user != None:
            self.fields['team_to_join'].queryset = Team.objects.filter(team_members=self.user)
    
    def send_invite(self):
        """Create a new invite and send it to each user"""

        users = self.cleaned_data.get("invited_users")

        invite = Invite.objects.create(
            invite_message=self.cleaned_data.get("invite_message"),
            inviting_team=self.cleaned_data.get("team_to_join")
        )
        invite.set_invited_users(users)

        return invite

class RemoveMemberForm(forms.Form):
    """Form enabling a team creator to remove a team member"""

    class Meta:
        """Form options."""
        fields = ['member_to_remove']

    member_to_remove = forms.ModelChoiceField(queryset=User.objects.all(), required=True)
    #thing = forms.CharField(max_length=50, choic)

    def __init__(self, *args, **kwargs):
        """Makes sure only members of current team (not including the creator)"""

        self.creator = kwargs.get("user")
        self.team = kwargs.get("team")
        if self.creator != None:
            kwargs.pop("user") 
        if self.team != None:
            kwargs.pop("team")

        super().__init__(*args, **kwargs)

        if self.creator != None and self.team != None:
            """Set the query set to be all members of team excluding the creator"""
            query_set = self.team.get_team_members()
            self.fields["members_to_invite"].queryset = query_set.exclude(id=self.creator.id)

    def remove_member(self):
        """Remove member from team"""
        pass

class DeleteTeamForm(forms.Form):
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'confirmClass'})
    )

class LaneForm(forms.ModelForm):
    """Form enabling a user to create a lane in the dashboard"""

    class Meta:
        model = Lane
        fields = ['lane_name', 'lane_id']
    
class LaneDeleteForm(forms.Form):
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'confirmClass'})
    )

class AssignTaskForm(forms.Form):
    """Form enabling a user to assign a task to another user in team"""

    class Meta:
        """Form options."""

        fields = ['team_members', 'task']

    team_members = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=True)

    def __init__(self, *args, **kwargs):
        """Show all the users who are part of the current team"""

        self.team = kwargs.get("team")
        self.task_name = kwargs.get("task_name")
        self.user = kwargs.get("user")

        if self.team != None:
            kwargs.pop("team")
        if self.task_name != None:
            kwargs.pop("task_name")
        if self.user != None:
            kwargs.pop("user")

        super().__init__(*args, **kwargs)

        if self.team != None:  
            self.fields["team_members"].queryset = self.team.get_team_members()
    
    def assign_task(self):
        """Assign the task to the team members selected"""

        task = Task.objects.get(name=self.task_name)
        assigned_users = self.cleaned_data.get("team_members")
        task.set_assigned_users(assigned_users)
        task.save()
