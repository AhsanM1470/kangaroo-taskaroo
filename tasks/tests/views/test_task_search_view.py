from django.test import TestCase
from django.urls import reverse
from tasks.models import Task, Lane, Team, User
from tasks.tests.helpers import LogInTester

class TaskSearchViewTests(TestCase, LogInTester):
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]
    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.team = Team.objects.create(
            team_name = 'test-team',
            team_creator= self.user,
            description = "A random test team"
        )
        self.lane = Lane.objects.create(
            lane_id = 1,
            team=self.team
        )
        Task.objects.create(name="Task 1", description="Description 1", due_date="2023-12-01", priority='low', lane=self.lane, assigned_team=self.team)
        Task.objects.create(name="Task 2", description="Description 2", due_date="2023-12-02", priority='medium', lane=self.lane,assigned_team=self.team)
        Task.objects.create(name="Task 3", description="Description 3", due_date="2023-12-03", priority='high', lane=self.lane,assigned_team=self.team)

    def test_search_view_with_results(self):
        response = self.client.get(reverse('task_search'), {'q': 'Task 1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Task 1')
        self.assertContains(response, 'Description 1')
        self.assertEqual(response.context['data'][0].due_date.__str__(), '2023-12-01 00:00:00+00:00')

    def test_search_view_no_results(self):
        response = self.client.get(reverse('task_search'), {'q': 'Non-existent task'})
        self.assertNotContains(response, "Task 1")
        self.assertNotContains(response, "Task 2")
        self.assertNotContains(response, "Task 3")
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
    
    def test_empty_search(self):
        # Test search with empty query
        response = self.client.get(reverse('task_search'))
        self.assertContains(response, "Task 1")
        self.assertContains(response, "Task 2")
        self.assertContains(response, "Task 3")






