from django.test import TestCase
from django.urls import reverse
from tasks.models import Task, Lane, Team, User
from tasks.tests.helpers import LogInTester

class TaskSearchViewTests(TestCase, LogInTester):
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_lane.json',
        'tasks/tests/fixtures/other_tasks.json',
    ]
    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.lane = Lane.objects.get(pk=1)
        self.team = Team.objects.get(pk=1)
        
        self.task = Task.objects.get(pk=3)
        self.task2 = Task.objects.get(pk=4)
        self.task3 = Task.objects.get(pk=5)

    def test_search_view_with_results(self):
        response = self.client.get(reverse('task_search'), {'q': 'Task3'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Task3')
        self.assertContains(response, "Annas 3rd task")
        self.assertEqual(response.context['data'][0].due_date.__str__(), '2023-12-01 00:00:00+00:00')

    def test_search_view_no_results(self):
        response = self.client.get(reverse('task_search'), {'q': 'Non-existent task'})
        self.assertNotContains(response, "Task5")
        self.assertNotContains(response, "Task2")
        self.assertNotContains(response, "Task3")
        self.assertNotContains(response, "Task4")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No tasks found.')

    def test_order_by_due_date_asc(self):
        response = self.client.get(reverse('task_search'), {'sort_column': 'due_date', 'sort_direction': 'asc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task3", "Task4", "Task5", "Task2"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)


    def test_order_by_due_date_desc(self):
        response = self.client.get(reverse('task_search'), {'sort_column': 'due_date', 'sort_direction': 'desc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task2", "Task5", "Task4", "Task3"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)

    def test_order_by_priority_asc(self):
        response = self.client.get(reverse('task_search'), {'sort_column': 'priority', 'sort_direction': 'asc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task3", "Task2", "Task4", "Task5"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)

    def test_order_by_priority_desc(self):
        response = self.client.get(reverse('task_search'), {'sort_column': 'priority', 'sort_direction': 'desc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task5", "Task2", "Task4", "Task3"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)
    
    def test_empty_search(self):
        # Test search with empty query
        response = self.client.get(reverse('task_search'))
        self.assertContains(response, "Task3")
        self.assertContains(response, "Task2")
        self.assertContains(response, "Task4")
        self.assertContains(response, "Task5")






