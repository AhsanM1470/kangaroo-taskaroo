from django.test import TestCase, Client
from tasks.models import Task, User

class TaskAdminTest(TestCase):
    
    fixtures = [
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_lane.json',
        'tasks/tests/fixtures/default_task.json',
    ]
    
    def setUp(self):
        self.user = User.objects.create_superuser(username='@testadmin', password='adminpass', email='testadmin@example.com')

    def test_user_admin_list_display(self):
        # Log in as the superuser
        self.client = Client()
        self.client.login(username='@testadmin', password='adminpass')

        # Access the admin page for the User model
        response = self.client.get('/admin/tasks/user/')

        # Check that the user is listed with the expected columns
        self.assertContains(response, '@janedoe')
        self.assertContains(response, 'Jane')
        self.assertContains(response, 'Doe')
        self.assertContains(response, 'janedoe@example.org')

    def test_task_admin_list_display(self):
        # Log in as the superuser
        self.client = Client()
        self.client.login(username='@testadmin', password='adminpass')

        # Access the admin page for the Task model
        response = self.client.get('/admin/tasks/task/')

        self.assertContains(response, 'Task1')


