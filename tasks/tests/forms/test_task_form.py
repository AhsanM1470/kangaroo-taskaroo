"""Unit tests of the task form."""
from django import forms
from django.test import TestCase
from tasks.forms import TaskForm
from tasks.models import Task, Lane, User, Team
from datetime import date, time, timezone, datetime
from django.utils import timezone

class TaskFormTestCase(TestCase):
    """Unit tests of the task form."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]

    def setUp(self):
        
        self.user = User.objects.get(username='@johndoe')
        
        self.team = Team.objects.create(
            team_name = 'Team1',
            team_creator = self.user
        )
        
        self.lane = Lane.objects.create(
            lane_name = 'TestLane',
            lane_id = 1,
            lane_order = 1,
            team = self.team
        )
        
        self.form_input = {
            'name': 'Task5',
            'description': 'Amys fifth task within task manager!',
            'date_field': timezone.datetime(2024, 12, 28, 10, 0, tzinfo=timezone.utc),
            'priority':'medium',
            'time_field': '10:05:00',
            'lane': self.lane,
            'assigned_team' : self.team
        }

    def test_valid_sign_up_form(self):
        form = TaskForm(data=self.form_input)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_has_necessary_fields(self):
        form = TaskForm()
        self.assertIn('name', form.fields)
        self.assertIn('description', form.fields)
        self.assertIn('date_field', form.fields)
        self.assertIn('time_field', form.fields)
        date_field = form.fields['date_field']
        self.assertTrue(isinstance(date_field, forms.DateField))
        time_field = form.fields['time_field']
        self.assertTrue(isinstance(time_field, forms.TimeField))
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
        self.form_input['date_field'] = date(2023, 12, 19)
        form = TaskForm(data=self.form_input)
        before_count = Task.objects.count()
        form.save()
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data['date_field'], self.form_input['date_field'])
        
        after_count = Task.objects.count()
        self.assertEqual(after_count, before_count+1)
        task = Task.objects.get(name='Task5')
        self.assertEqual(task.description, 'Amys fifth task within task manager!')
        expected_due_date = datetime.strptime('2023-12-19 10:05', '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
        self.assertEqual(task.due_date, expected_due_date)

    def test_invalid_task_name_too_short(self):
        self.form_input['name'] = 'T1'
        form = TaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['name'], [
            'Enter a valid word with at least 3 alphanumeric characters (no special characters allowed).'])

    def test_valid_name_with_space(self):
        self.form_input['name'] = 'Tasks name with space'
        form = TaskForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_invalid_past_date_and_time_combination(self):
        self.form_input['date_field'] = date(2020, 12, 19)
        self.form_input['time_field'] = '10:06:00'
        form = TaskForm(data=self.form_input)
        self.assertFalse(form.is_valid())
        self.assertIn('date_field', form.errors)
        self.assertEqual(form.errors['date_field'], ['Pick a date-time in the future!'])
