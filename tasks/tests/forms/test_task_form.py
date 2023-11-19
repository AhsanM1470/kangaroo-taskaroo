"""Unit tests of the task form."""
from django import forms
from django.test import TestCase
from tasks.forms import TaskForm
from tasks.models import Task
from datetime import datetime, timezone

class TaskFormTestCase(TestCase):
    """Unit tests of the task form."""

    def setUp(self):
        self.form_input = {
            'name': 'Task5',
            'description': 'Amys fifth task within task manager!',
            'due_date': '2023-12-19 15:30',
        }

    def test_valid_sign_up_form(self):
        form = TaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_has_necessary_fields(self):
        form = TaskForm()
        self.assertIn('name', form.fields)
        self.assertIn('description', form.fields)
        self.assertIn('due_date', form.fields)
        due_date_field = form.fields['due_date']
        self.assertTrue(isinstance(due_date_field, forms.DateTimeField))
        description_widget = form.fields['description'].widget
        self.assertTrue(isinstance(description_widget, forms.Textarea))

    def test_form_uses_model_validation(self):
        self.form_input['name'] = ''
        form = TaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_name_cannot_contain_special_characters(self):
        self.form_input['name'] = '@@@'
        form = TaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_must_save_correctly(self):
        form = TaskForm(data=self.form_input)
        before_count = Task.objects.count()
        form.save()
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count+1)
        task = Task.objects.get(name='Task5')
        self.assertEqual(task.description, 'Amys fifth task within task manager!')
        expected_due_date = datetime.strptime('2023-12-19 15:30', '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
        self.assertEqual(task.due_date, expected_due_date)