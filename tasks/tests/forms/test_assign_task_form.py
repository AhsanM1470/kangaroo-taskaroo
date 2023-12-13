"""Unit tests of the assign task form."""
from django.test import TestCase
from tasks.forms import AssignTaskForm
from tasks.models import User, Task

class AssignTaskFormTestCase(TestCase):
    """Unit tests of the Assign Task form."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/default_lane.json',
        'tasks/tests/fixtures/default_task.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")
        self.form_input = {     
            'team_members': [self.user, self.other_user]
        }

    def test_form_has_necessary_fields(self):
        form = AssignTaskForm()
        self.assertIn('team_members', form.fields)

    def test_valid_assign_task_form(self):
        form = AssignTaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_must_save_correctly(self):
        """Check if the form assigns the tasks to each user"""
        task = Task.objects.get(id=1)
        form = AssignTaskForm(task=task, data=self.form_input)
        self.assertTrue(form.is_valid())
        before_count = Task.objects.count()
        form.assign_task()
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertTrue(task in self.user.get_tasks())
        self.assertTrue(task in self.other_user.get_tasks())
    
    def test_only_team_members_are_shown_as_choices(self):
        """Check if form only shows team members as choices to assign task"""
        task = Task.objects.get(id=1)
        team = task.assigned_team
        form = AssignTaskForm(team=team, task=task)
        self.assertFalse(form.is_valid())
        team_member_choices = form.fields["team_members"].queryset

        for team_member in team_member_choices:
            self.assertTrue(team_member in team.get_team_members())

    def test_already_assigned_users_are_selected_initially(self):
        """Check that previously assigned users are already ticked in form"""
        task = Task.objects.get(id=1)
        form = AssignTaskForm(task=task, data=self.form_input)
        self.assertTrue(form.is_valid())
        form.assign_task()
        new_form = AssignTaskForm(task=task)
        self.assertTrue(self.user in new_form.fields["team_members"].initial)
        self.assertTrue(self.other_user in new_form.fields["team_members"].initial)
