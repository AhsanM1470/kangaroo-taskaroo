"""Unit tests for the Task model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import Task, Lane, Team, User
from datetime import datetime, timedelta
from django.utils import timezone
import pytz

class TaskModelTestCase(TestCase):
    """Unit tests for the Task model."""
    
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_lane.json',
        'tasks/tests/fixtures/default_task.json',
        'tasks/tests/fixtures/other_tasks.json'
    ]
    
    def setUp(self):
        
        self.timezone_utc = pytz.timezone('UTC')
        
        self.user = User.objects.get(username='@johndoe')
        self.user2 = User.objects.get(username='@janedoe')
        self.user3 = User.objects.get(username='@petrapickles')
        self.user4 = User.objects.get(username='@peterpickles')
        
        self.task = Task.objects.get(pk=1) 
        self.task.assigned_users.add(self.user3)
        self.task2 = Task.objects.get(pk=2) 
        self.lane = Lane.objects.get(pk=1)
        self.team = Team.objects.get(pk=1)
        
    def test_valid_task(self):
        self._assert_task_is_valid(self.task)
        
    # Name Tests
    
    def test_name_cannot_be_none(self):
        self.task.name = None
        self._assert_task_is_invalid(self.task)
        
    def test_name_can_be_30_characters_long(self):
        self.task.name = '1' * 15 + 'x' * 14 + ' '
        self._assert_task_is_valid(self.task)
    
    def test_name_cannot_be_over_30_characters_long(self):
        self.task.name = '1' * 15 + ' ' + 'x' * 15
        self._assert_task_is_invalid(self.task)
        
    def test_name_can_be_duplicate(self):
        self.task2.name = 'Task1'
        self.task2.full_clean()
        self._assert_task_is_valid(self.task2)
        
    def test_name_must_only_contain_alphanumericals(self):
        self.task.name = 'Ta-sk1'
        self._assert_task_is_invalid(self.task)
        
    def test_name_must_contain_at_least_3_alphanumericals(self):
        self.task.name = 'Ta'
        self._assert_task_is_invalid(self.task)
        
    # Description Tests
    
    def test_description_can_be_blank(self):
        self.task.description = None
        self._assert_task_is_valid(self.task)
        
    def test_description_may_already_exist(self):
        self.task.description = 'Description'
        self.task2.description = 'Description'
        self._assert_task_is_valid(self.task)
        
    def test_description_can_be_530_characters_long(self):
        self.task.description = '1' + 'x' * 529
        self._assert_task_is_valid(self.task)
        
    def test_description_cannot_be_over_530_characters_long(self):
        self.task.description = '1' + 'x' * 530
        self._assert_task_is_invalid(self.task)
        
    # Due Date Tests
    
    def test_due_date_cannot_be_in_the_past(self):
        self.task.due_date = timezone.datetime(2000, 11, 28, 10, 0, tzinfo=timezone.utc)
        self._assert_task_is_invalid(self.task)
        
    def test_due_date_can_be_in_the_future(self):
        self._assert_task_is_valid(self.task)
    
    def test_due_date_cannot_be_blank(self):
        self.task.due_date = None
        self._assert_task_is_invalid(self.task)
        
    # Lane Tests
    
    def test_query_tasks_by_lane(self):
        tasks_by_lane = Task.objects.filter(lane=self.lane)
        self.assertEqual(tasks_by_lane.count(), 2)
        
    def test_delete_lane_cascades_to_tasks(self):
        self.lane.delete()
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(pk=self.task.pk)
            
    def test_lane_cannot_be_blank(self):
        self.task.lane = None
        self._assert_task_is_invalid(self.task)
        
    # Assigned Team Tests
    
    def test_query_tasks_by_team(self):
        tasks_by_team = Task.objects.filter(assigned_team=self.team)
        self.assertEqual(tasks_by_team.count(), 2)
        
    def test_delete_team_cascades_to_tasks(self):
        self.team.delete()
        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(pk=self.task.pk)
            
    def test_team_cannot_be_blank(self):
        self.task.assigned_team = None
        self._assert_task_is_invalid(self.task)
        
    # Assigned Users Tests
    
    def test_add_users_to_tasks(self):
        self.task.assigned_users.add(self.user, self.user4)
        
        self.assertEqual(self.task.assigned_users.count(), 3)
        self.assertIn(self.user, self.task.assigned_users.all())
        self.assertIn(self.user4, self.task.assigned_users.all())
        
    def test_query_tasks_by_user(self):
        self.task.assigned_users.add(self.user)
        self.task2.assigned_users.add(self.user2, self.user)
        
        user_assigned_tasks = Task.objects.filter(assigned_users= self.user)
        
        self.assertEqual(user_assigned_tasks.count(), 2)
        self.assertEqual(user_assigned_tasks[0], self.task)
        self.assertEqual(user_assigned_tasks[1], self.task2)
        
    def test_assigned_users_can_be_blank(self):
        self._assert_task_is_valid(self.task2)
        
    # Dependencies Tests
    
    def test_create_task_with_dependancies(self):
        task3 = Task.objects.create(
            name = 'Task2',
            description = 'Amys second task within task manager!',
            due_date = timezone.datetime(2024, 12, 28, 10, 0, tzinfo=timezone.utc),
            lane = self.lane,
            assigned_team = self.team
        )
        
        self.task.dependencies.add(self.task2, task3)
        self.assertIn(self.task2, self.task.dependencies.all())
        self.assertIn(task3, self.task.dependencies.all())
        
    def test_task_valid_with_no_dependancies(self):
        task3 = Task.objects.create(
            name = 'Task2',
            description = 'Amys second task within task manager!',
            due_date = timezone.datetime(2024, 12, 28, 10, 0, tzinfo=timezone.utc),
            lane = self.lane,
            assigned_team = self.team
        )
        
        self._assert_task_is_valid(task3)
        
    # Deadline Notif Sent Tests
    
    def test_deadline_notif_sent_default(self):
        expected_default_value = (datetime.today() - timedelta(days=1)).date()
        actual_default_value = self.task.deadline_notif_sent
        self.assertEqual(actual_default_value, expected_default_value)

    def test_changed_deadline_notif_sent(self):
        self.task.assigned_team.add_invited_member(self.user)
        self.task.due_date = timezone.make_aware((datetime.today()+timedelta(days=5)), self.timezone_utc)
        self.task.notify_keydates()
        self.assertEqual(self.task.deadline_notif_sent,datetime.today().date())
        
    # Assertions:
    
    def _assert_task_is_valid(self, task):
        try:
            task.full_clean()
        except ValidationError:
            self.fail('Test task should be valid')
            
    def _assert_task_is_invalid(self, task):
        with self.assertRaises(ValidationError):
            task.full_clean()