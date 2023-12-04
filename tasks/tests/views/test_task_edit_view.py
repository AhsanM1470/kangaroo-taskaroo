from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Task
from datetime import datetime
from tasks.forms import TaskForm
from django.contrib.auth import get_user_model

class TaskEditViewTestCase(TestCase, LogInTester):
    """Tests of the task edit view."""
    def setUp(self):
       
        username_to_find = '@johndoe'
        self.user = get_user_model().objects.create_user(username=username_to_find, password='Password123')
        
        self.task = Task.objects.create(
            name='Test Task',
            description = 'Some random task, idk anymore',
            due_date = datetime(2024,1,19,10,5)
        )
        self.form_input = {
            'name': 'SpecialTask',
            'description': 'Amys special task within task manager!',
            'date_field': '2023-12-19',
            'time_field': '10:05'
        }
        self.url = reverse('task_edit', kwargs={'task_name': self.task.name})
        self.client.login(username=self.user.username, password='Password123')

    def test_login_user(self):
        # Log in the user using the test client
        logged_in = self.client.login(username='@johndoe', password='Password123')

        # Check if login was successful
        self.assertTrue(logged_in)

    def test_task_edit_url(self):
        self.assertEqual(self.url,'/task_edit/Test Task/')


    def test_get_task(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task_edit.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, TaskForm))
        self.assertFalse(form.is_bound)
        self.assertTrue('name' in form.fields)
        self.assertEqual(form['name'].value(), 'Test Task')
        self.assertTrue('description' in form.fields)
        self.assertEqual(form['description'].value(), 'Some random task, idk anymore')
        self.assertTrue('date_field' in form.fields)
        self.assertEqual(form['date_field'].value(), '2024-')

    # def test_successful_task_edit(self):
    #     before_count = Task.objects.count()
    #     response = self.client.post(self.url, data=self.form_input, follow=True)
    #     after_count = Task.objects.count()
    #     self.assertEqual(after_count, before_count + 1)
    #     redirect_url = reverse('dashboard')
    #     self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
    #     self.assertTemplateUsed(response, 'dashboard.html')
    #     created_task = Task.objects.filter(name='SpecialTask').first()
    #     self.assertIsNotNone(created_task, "SpecialTask should be created")
    #     self.assertEqual(created_task.description, 'Amys special task within task manager!')
        
    # def test_unsuccesful_task_create(self):
    #     self.task_data_bad = {
    #         'name': 'Ta',
    #         'description': 'Amys fifth task within task manager!',
    #         'due_date': '2023-12-19 15:30',
    #     }
    #     before_count = Task.objects.count()
    #     response = self.client.post(self.url, self.task_data_bad)
    #     after_count = Task.objects.count()
    #     self.assertEqual(after_count, before_count)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'task_create.html')
    #     form = response.context['form']
    #     self.assertTrue(isinstance(form, TaskForm))
    #     self.assertTrue(form.is_bound)
    #     self.assertFalse(Task.objects.filter(name='Ta').exists())


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

        
    