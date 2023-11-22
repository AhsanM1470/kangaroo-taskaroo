"""Unit tests for the Task model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import Task
from datetime import datetime

class TaskModelTestCase(TestCase):
    """Unit tests for the Task model."""
    def setUp(self):
        self.task = Task.objects.create(
            name = 'Task1',
            description = 'Amys first task within task manager!',
            due_date = datetime.datetime(2023, 11, 28, 10, 0),
        )
        
        self.task2 = Task.objects.create(
            name = 'Task2',
            description = 'Amys second task within task manager!',
            due_date = datetime.datetime(2023, 12, 28, 10, 0),
        )
        
    def test_valid_user(self):
        self._assert_task_is_valid
        
    # Name Tests
    
    def test_name_cannot_be_blank(self):
        self.task.name = ''
        self._assert_task_is_invalid
        
    def test_name_can_be_30_characters_long(self):
        self.task.name = '1' * 15 + 'x' * 15
        self._assert_task_is_valid
    
    def test_name_cannot_be_over_30_characters_long(self):
        self.task.name = '1' * 15 + 'x' * 16
        self._assert_task_is_invalid
        
    def test_name_must_be_unique(self):
        self.task2.name = 'Task1'
        self.task.name = 'Task1'
        self._assert_task_is_invalid
        
    def test_name_must_only_contain_alphanumericals(self):
        self.task.name = 'Ta-sk1'
        self._assert_task_is_invalid
        
    def test_name_must_contain_at_least_3_alphanumericals(self):
        self.task.name = 'Ta'
        self._assert_task_is_invalid
        
    # Description Tests
    
    def test_description_can_be_blank(self):
        self.task.description = ''
        self._assert_task_is_valid
        
    def test_description_may_already_exist(self):
        self.task.description = 'Description'
        self.task2.description = 'Description'
        self._assert_task_is_valid
        
    def test_description_can_be_530_characters_long(self):
        self.task.description = '1' + 'x' * 529
        self._assert_task_is_valid
        
    def test_description_cannot_be_over_530_characters_long(self):
        self.task.description = '1' + 'x' * 530
        self._assert_task_is_invalid
        
    # Due Date Tests
    
    # I dont know what tests to do, not sure if i can test if due_date is after created_at     
        
    # Assertions:
    
    def _assert_task_is_valid(self):
        try:
            self.task.full_clean()
        except ValidationError:
            self.fail('Test task should be valid')
            
    def _assert_task_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.task.full_clean()