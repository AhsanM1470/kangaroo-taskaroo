from django.contrib import admin
from .models import User, Team, Invite, Task

# Register your models here.

"""These haven't been fully finished, but seem to work for what is needed so far"""

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Configuration of the adminstrative interface for users"""
    list_display = [
        "username", "first_name", "last_name", "email", "is_active", "get_invites", "get_created_teams", "get_tasks", "get_teams"
    ]

    def get_invites(self, user):
        return [invite.inviting_team for invite in user.get_invites()]
    
    def get_created_teams(self, user):
        return [team for team in user.get_created_teams()]

    def get_tasks(self, user):
        return [task for task in user.get_tasks()]

    def get_teams(self, user):
        return [team for team in user.get_teams()]

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Configuration of the adminstrative interface for users"""
    list_display = [
        "team_name", "get_members", "description", "get_tasks"
    ]

    def get_members(self, team):
        return [user.username for user in team.get_team_members().all()]

    def get_tasks(self, team):
        return [task for task in team.get_tasks()]


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    """Configuration of the adminstrative interface for invites"""
    list_display = [
        "get_invited_users", "get_team", "invite_message"
    ]

    def get_invited_users(self, invite):
        return [user.username for user in invite.invited_users.all()]
    
    
    def get_team(self, invite):
        return [invite.inviting_team]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "name", "description", "due_date", "created_at", "assigned_team", "get_assigned_users"
    ]

    def get_assigned_users(self, task):
        return [user for user in task.get_assigned_users()]