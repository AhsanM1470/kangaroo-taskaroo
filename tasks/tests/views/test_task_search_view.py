from django.test import TestCase
from django.urls import reverse
from tasks.models import Task
from tasks.tests.helpers import LogInTester

class TaskSearchViewTests(TestCase, LogInTester):
    def setUp(self):
        Task.objects.create(name="Task 1", description="Description 1", due_date="2023-12-01", priority='low')
        Task.objects.create(name="Task 2", description="Description 2", due_date="2023-12-02", priority='medium')
        Task.objects.create(name="Task 3", description="Description 3", due_date="2023-12-03", priority='high')

    def test_search_view_with_results(self):
        response = self.client.get(reverse('task_search'), {'q': 'Task 1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Task 1')
        self.assertContains(response, 'Description 1')
        self.assertEquals(response.context['data'][0].due_date.__str__(), '2023-12-01 00:00:00+00:00')

    def test_search_view_no_results(self):
        response = self.client.get(reverse('task_search'), {'q': 'Non-existent task'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No tasks found.')

    def test_order_by_due_date_asc(self):
        response = self.client.get(reverse('task_search'), {'sort_column': 'due_date', 'sort_direction': 'asc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task 1", "Task 2", "Task 3"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)


    def test_order_by_due_date_desc(self):
        response = self.client.get(reverse('task_search'), {'sort_column': 'due_date', 'sort_direction': 'desc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task 3", "Task 2", "Task 1"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)

    def test_order_by_priority_asc(self):
        response = self.client.get(reverse('task_search'), {'sort_column': 'priority', 'sort_direction': 'asc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task 1", "Task 2", "Task 3"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)

    def test_order_by_priority_desc(self):
        response = self.client.get(reverse('task_search'), {'sort_column': 'priority', 'sort_direction': 'desc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task 3", "Task 2", "Task 1"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)







