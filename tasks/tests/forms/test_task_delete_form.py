"""Unit tests of the task delete form."""
from django import forms
from django.test import TestCase
from tasks.forms import TaskDeleteForm
from tasks.models import Task
from datetime import date, time, timezone, datetime

class TaskFormTestCase(TestCase):
    """Unit tests of the task delete form."""
    
    fixtures = [
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_lane.json',
        'tasks/tests/fixtures/default_task.json',
    ]

    def setUp(self):
        self.task = Task.objects.get(pk=1)
        self.form_input = {
            'confirm_deletion': True
        }

    def test_valid_task_deletion_form(self):
        form = TaskDeleteForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_invalid_task_deletion_form(self):
        self.form_input = {}
        form = TaskDeleteForm(data=self.form_input)
        self.assertFalse(form.is_valid())