from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Task, Team, User
from tasks.forms import CreateTeamForm
from urllib.parse import unquote

class TaskCreateTeamViewTestCase(TestCase, LogInTester):
    """Tests of the assign task view."""
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_task.json',
        'tasks/tests/fixtures/default_lane.json'
    ]
    
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.other_user = User.objects.get(username='@janedoe')
        self.team = Team.objects.get(pk=1)
        self.team.add_invited_member(self.team.team_creator)
        self.team.add_invited_member(self.user)
        self.team.add_invited_member(self.other_user)
        self.team.save()

        self.task = Task.objects.get(pk=1)
        self.url = reverse('assign_task', kwargs={'task_id': self.task.id})

        self.form_input = {     
            'team_members': [self.user.id, self.other_user.id]
        }
        self.client.login(username=self.user.username, password='Password123')

        session = self.client.session
        session["current_team_id"] = self.team.id
        session.save()

    def test_assign_task_url(self):
        self.assertEqual(unquote(self.url),f'/assign_task/1/')

    def test_get_assign_task(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assign_task.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, CreateTeamForm))
        self.assertFalse(form.is_bound)
    
    def test_successful_assign_task(self):
        before_count = Task.objects.count()
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertTrue(self.task in self.user.get_tasks())
        self.assertTrue(self.task in self.other_user.get_tasks())