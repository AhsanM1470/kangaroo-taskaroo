"""Forms for the tasks app."""
from django import forms
from django.contrib.auth import authenticate
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import User, Task, Team, Invite
from django.utils import timezone
from datetime import datetime


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
        fields = ["name", "description"]
        widgets = {
            'name' : forms.TextInput(attrs={'class': 'nameClass', 'placeholder': 'Enter the task name...'}),
            'description' : forms.Textarea(attrs={'class': 'descriptionClass', 'placeholder': 'Write a task description...'})
        }
     
    date_field = forms.DateField(
        label='Date',
        widget=forms.SelectDateWidget(),
    )
    time_field = forms.TimeField(
        label='Time',
        widget=forms.TimeInput(attrs={'placeholder': '00:00:00'}),
    )
        
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
                raise ValidationError('Pick a date-time in the future!')
        return cleaned_data
    
    def save(self, commit=True):
        instance = super(TaskForm, self).save(commit=False)
        date = self.cleaned_data.get('date_field')
        time = self.cleaned_data.get('time_field')

        if date is not None and time is not None:
            instance.due_date = datetime.combine(date, time)
        
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
        fields = ['team_name', 'description', 'team_members']
    
    def create_team(self, user):
        """Create a new team"""

        team_members = self.cleaned_data.get("team_members")
        # Maybe for each team member, send them an invite instead of doing it automatically
        
        team = Team.objects.create(
            team_name=self.cleaned_data.get("team_name"),
            description=self.cleaned_data.get("description"),
        )
        team.add_creator(user) # This user is the first member of the team

        if len(team_members) != 0: # If you had members you added in the form
            team.add_team_member(team_members) 
        return team

class InviteForm(forms.ModelForm):
    """Form enabling a user to create and send an invite to another user"""

    class Meta:
        """Form options."""

        model = Invite
        fields = ['invited_users', 'invite_message', "team_to_join"]
    
    team_to_join = forms.ModelChoiceField(queryset=Team.objects.all())
    
    def __init__(self, user=None, **kwargs):
        """Makes sure only teams that the current user belongs to are given as options"""

        super().__init__(**kwargs)
        self.user = user
        
        if self.user != None:
            self.fields['team_to_join'].queryset.filter(team_members=self.user)
    
    def send_invite(self):
        """Create a new invite"""

        users = self.cleaned_data.get("invited_users")
        team = self.cleaned_data.get("team_to_join")
        # Need to change this so that all the users and the team is passed into the invite object

        invite = Invite.objects.create(
            invite_message=self.cleaned_data.get("invite_message")
        )
        invite.set_invited_users(users)
        invite.set_team(team)
        invite.save()

        return invite
