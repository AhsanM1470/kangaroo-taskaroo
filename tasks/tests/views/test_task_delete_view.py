from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Task
from datetime import datetime
from tasks.forms import TaskDeleteForm
from django.contrib.auth import get_user_model
from urllib.parse import unquote

class TaskDeleteViewTestCase(TestCase, LogInTester):
    """Tests of the task delete view."""
    def setUp(self):
       
        username_to_find = '@johndoe'
        self.task = Task.objects.create(
            name='Test Task',
            description = 'Some random task, idk anymore',
            due_date = datetime(2024,1,19,10,5)
        )
        self.user = get_user_model().objects.create_user(username=username_to_find, password='Password123')
        self.url = reverse('task_delete', kwargs={'task_name': self.task.name})

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
        self.assertEqual(unquote(self.url),'/task_delete/Test Task/')

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
        self.assertEqual(after_count, before_count)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        deleted_task = Task.objects.filter(name='Test Task').first()
        self.assertIsNone(deleted_task, "Test Task should be deleted")
        
    def test_unsuccesful_task_create(self):
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
