from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Task, User, Lane, Team
from datetime import datetime, date, time
from tasks.forms import TaskForm
from django.contrib.auth import get_user_model


class TaskEditViewTestCase(TestCase, LogInTester):
    """Tests of the task edit view."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_lane.json',
        'tasks/tests/fixtures/default_task.json',
        'tasks/tests/fixtures/other_tasks.json'
    ]

    def setUp(self):
        username_to_find = '@johndoe'
        self.user = User.objects.get(username='@johndoe')
        
        self.task = Task.objects.get(pk=1) 
        self.task2 = Task.objects.get(pk=2) 
        self.lane = Lane.objects.get(pk=1)
        self.team = Team.objects.get(pk=1)
        self.form_input = {
            'name': 'SpecialTask',
            'description': 'Amys special task within task manager!',
            'date_field': '2024-12-19',
            'time_field': '10:05',
            'priority':'medium',
            'lane': self.lane,
            'assigned_team': self.team
        }
        self.url = reverse('task_edit', kwargs={'pk': self.task.pk})
        self.client.login(username=self.user.username, password='Password123')

    def test_login_user(self):
        # Log in the user using the test client
        logged_in = self.client.login(username='@johndoe', password='Password123')

        # Check if login was successful
        self.assertTrue(logged_in)

    def test_task_edit_url(self):
        self.assertEqual(self.url, f'/task_edit/{self.task.pk}/')

    def test_get_task(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_edit.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, TaskForm))
        self.assertFalse(form.is_bound)
        self.assertTrue('name' in form.fields)
        self.assertEqual(form['name'].value(), 'Task1')
        self.assertTrue('description' in form.fields)
        self.assertEqual(form['description'].value(), "Amy's 69th task within task manager!")
        self.assertTrue('date_field' in form.fields)
        self.assertEqual(form['date_field'].value(), date(2024, 11, 28))
        self.assertTrue('time_field' in form.fields)
        self.assertEqual(form['time_field'].value(), time(10, 0, 0))

    def test_successful_task_edit(self):
        session = self.client.session
        session["current_team_id"] = self.team.pk
        session.save()
        before_count = Task.objects.count()
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count)
        new_task = Task.objects.filter(name='SpecialTask').first()
        old_task = Task.objects.filter(name='Task1').first()
        self.assertIsNotNone(new_task, "SpecialTask should be the new name")
        self.assertIsNone(old_task, "Test Task should be updated")
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_unsuccesful_task_edit(self):
        self.task_data_bad = {
            'name': 'Ta',
            'date_field': '2023-11-19',
            'time_field': '10:05'
        }
        before_count = Task.objects.count()
        response = self.client.post(self.url, self.task_data_bad)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_edit.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, TaskForm))
        self.assertTrue(form.is_bound)
        self.assertFalse(Task.objects.filter(name='Ta').exists())

    def test_successful_task_edit_with_duplicate_names(self):
        session = self.client.session
        session["current_team_id"] = self.team.pk
        session.save()
        self.form_input['name'] = 'Task1'
        before_count = Task.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        form = response.context['create_task_form']
        self.assertTrue(isinstance(form, TaskForm))
        self.assertFalse(form.is_bound)




