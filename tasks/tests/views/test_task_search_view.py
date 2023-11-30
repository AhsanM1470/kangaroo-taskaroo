from django.test import TestCase
from django.urls import reverse
from tasks.models import Task
from tasks.tests.helpers import LogInTester
from datetime import datetime

from django.http import HttpResponseBadRequest

class TaskSearchViewTests(TestCase, LogInTester):
    def setUp(self):
        Task.objects.create(name="Task 1", description="Description 1", due_date="2023-12-01")
        Task.objects.create(name="Task 2", description="Description 2", due_date="2023-12-02")
        Task.objects.create(name="Task 3", description="Description 3", due_date="2023-12-03")

    def test_search_view_with_results(self):
        response = self.client.get(reverse('task_search'), {'q': 'Task 1'})
        #print(response.content)
        self.assertEqual(response.status_code, 200)
        for x in response.context:
            print(x)

        print(response.context['data'][0].due_date)
        self.assertContains(response, 'Task 1')
        self.assertContains(response, 'Description 1')
        self.assertContains(response, '2023-12-01 00:00:00+00:00')

    def setUp(self):
        Task.objects.create(name="Task 1", description="Description 1", due_date="2023-12-01")
        Task.objects.create(name="Task 2", description="Description 2", due_date="2023-12-02")
        Task.objects.create(name="Task 3", description="Description 3", due_date="2023-12-03")

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
        response = self.client.get(reverse('task_search'), {'sort_due_date': 'asc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task 1", "Task 2", "Task 3"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)

    def test_order_by_due_date_desc(self):
        response = self.client.get(reverse('task_search'), {'sort_due_date': 'desc'})
        self.assertEqual(response.status_code, 200)
        tasks = response.context['data']
        expected_order = ["Task 3", "Task 2", "Task 1"]
        actual_order = [task.name for task in tasks]
        self.assertEqual(actual_order, expected_order)

    # def test_invalid_sort_parameter(self):
    #     response = self.client.get(reverse('task_search'), {'sort_due_date': 'invalid'})
    #     print(response.content.decode('utf-8'))
    #     self.assertContains(response, "Invalid value for 'sort_due_date'", status_code=400)
    #     self.assertIsInstance(response, HttpResponseBadRequest)
    #     self.assertContains(response, "Invalid value for 'sort_due_date'")



