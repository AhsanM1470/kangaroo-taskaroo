"""Unit tests of the task delete form."""
from django.test import TestCase
from tasks.forms import RemoveMemberForm
from tasks.models import Team

class RemoveMemberFormTestCase(TestCase):
    """Unit tests of the remove team member form."""
    
    fixtures = [
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
    ]

    def setUp(self):
        self.team = Team.objects.get(pk=1)
        self.form_input = {
            'confirm_deletion': True
        }

    def test_valid_task_deletion_form(self):
        form = RemoveMemberForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_invalid_task_deletion_form(self):
        self.form_input = {}
        form = RemoveMemberForm(data=self.form_input)
        self.assertFalse(form.is_valid())