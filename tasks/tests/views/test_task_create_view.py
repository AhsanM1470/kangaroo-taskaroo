from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Task, Team, User, Lane
from datetime import datetime, date
from tasks.forms import TaskForm
from django.contrib.auth import get_user_model

class TaskCreateViewTestCase(TestCase, LogInTester):
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
        self.url = reverse('task_create')

        self.team = Team.objects.get(pk=1)
        self.lane = Lane.objects.get(pk=1)
        
        self.form_input = {
            'name': 'SpecialTask',
            'description': 'Amys special task within task manager!',
            'date_field': date(2024, 12, 28),
            'priority':'medium',
            'time_field': '10:05:00',
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
        self.assertEqual(self.url,'/task_create/')


    def test_get_task(self):
        session = self.client.session
        session["current_team_id"] = self.team.pk
        session.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_create.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, TaskForm))
        self.assertFalse(form.is_bound)
       
    # def test_succesful_task_create(self):
    #     self.client.login(username=self.user.username, password='Password123')
    #     task = { 'name': 'Task1', 'description': 'Amys first task within task manager!' }
    #     response = self.client.post(self.url, task, follow=True)
    #     redirect_url = reverse('dashboard')
    #     self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)

    #     self.assertTemplateUsed(response, 'dashboard.html')

    def test_successful_task_create(self):
        session = self.client.session
        session["current_team_id"] = self.team.pk
        session.save()
        before_count = Task.objects.count()
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count + 1)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        created_task = Task.objects.filter(name='SpecialTask').first()
        self.assertIsNotNone(created_task, "SpecialTask should be created")
        self.assertEqual(created_task.description, 'Amys special task within task manager!')
        
    def test_unsuccesful_task_create(self):
        session = self.client.session
        session["current_team_id"] = self.team.pk
        session.save()
        self.task_data_bad = {
            'name': 'Ta',
            'description': 'Amys fifth task within task manager!',
            'due_date': '2023-12-19 15:30',
        }
        before_count = Task.objects.count()
        response = self.client.post(self.url, self.task_data_bad)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_create.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, TaskForm))
        self.assertTrue(form.is_bound)
        self.assertFalse(Task.objects.filter(name='Ta').exists())


    # def test_unsuccessful_task_create_due_to_duplicate_names(self):
    #     self.client.login(username=self.user.username, password='Password123')
    #     self.task_data['name'] = 'task1'
    #     before_count = Task.objects.count()
    #     response = self.client.post(self.url, self.task_data, follow=True)
    #     after_count = Task.objects.count()
    #     self.assertEqual(after_count, before_count)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'create_task.html')
    #     form = response.context['form']
    #     self.assertTrue(isinstance(form, TaskForm))
    #     self.assertFalse(form.is_bound)

        
    