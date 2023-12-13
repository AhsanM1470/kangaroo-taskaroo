from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Task, Team, User, Lane
from datetime import datetime, date
from tasks.forms import TaskForm
from django.contrib.auth import get_user_model

class TaskViewTestCase(TestCase, LogInTester):
    """Tests of the task form view."""
    
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_lane.json',
        'tasks/tests/fixtures/default_task.json',
    ]
    
    def setUp(self):

        self.user = User.objects.get(username='@johndoe')
        self.task = Task.objects.get(pk=1)
        self.url = reverse('task', kwargs={'pk': self.task.pk})

        self.team = Team.objects.get(pk=1)
        self.lane = Lane.objects.get(pk=1)
        
        self.form_input = {
            'name': 'SpecialTask',
            'description': 'Amys special task within task manager!',
            'date_field': date(2024, 12, 28),
            'priority':'medium',
            'time_field': '10:05:00',
            'lane': self.lane,
            'assigned_team' : self.team
        }
        
        self.client.login(username=self.user.username, password='Password123')
        self.client.session["current_team_id"] = self.team.id

    def test_login_user(self):
        # Log in the user using the test client
        logged_in = self.client.login(username='@johndoe', password='Password123')

        # Check if login was successful
        self.assertTrue(logged_in)

    def test_task_create_url(self):
        self.assertEqual(self.url,'/task/1/')
        
    def test_task_view_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
    def test_task_view_uses_context(self):
        response = self.client.get(self.url)
        self.assertIn('task', response.context)
        self.assertEqual(response.context['task'], self.task)


        
    