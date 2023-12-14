from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Task, Team, Lane, User
from datetime import datetime
from tasks.forms import TaskDeleteForm
from django.contrib.auth import get_user_model
from urllib.parse import unquote

class TaskDeleteViewTestCase(TestCase, LogInTester):
    """Tests of the task delete view."""
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]
    
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.create(
            team_name = 'test-team',
            team_creator= self.user,
            description = "A random test team"
        )
        self.team.add_invited_member(self.user)
        self.lane = Lane.objects.create(
            lane_id = 1,
            team=self.team
        )
        self.task = Task.objects.create(
            name='Test Task',
            description = 'A random test task',
            due_date = datetime(2024,1,19,10,5),
            assigned_team=self.team,
            lane = self.lane
        )
        self.url = reverse('task_delete', kwargs={'pk': self.task.pk})

        self.form_input = {
            'confirm_deletion': True
        }
        
        self.client.login(username=self.user.username, password='Password123')

    def test_login_user(self):
        # Log in the user using the test client
        logged_in = self.client.login(username='@johndoe', password='Password123')

        # Check if login was successful
        self.assertTrue(logged_in)

    def test_task_create_url(self):
        self.assertEqual(unquote(self.url),f'/task_delete/1/')

    def test_get_delete_task(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_delete.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, TaskDeleteForm))
        self.assertFalse(form.is_bound)
    
    def test_successful_task_delete(self):
        before_count = Task.objects.count()
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count-1)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        deleted_task = Task.objects.filter(name='Test Task').first()
        self.assertIsNone(deleted_task, "Test Task should be deleted")
        
    def test_unsuccesful_task_delete(self):
        self.task_data_bad = { }
        before_count = Task.objects.count()
        response = self.client.post(self.url, self.task_data_bad)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_delete.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, TaskDeleteForm))
        self.assertTrue(form.is_bound)
        self.assertTrue(Task.objects.filter(name='Test Task').exists())