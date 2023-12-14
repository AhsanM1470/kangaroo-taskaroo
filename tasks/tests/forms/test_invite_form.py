"""Unit tests of the invite form."""
from django import forms
from django.test import TestCase
from tasks.forms import InviteForm
from tasks.models import User, Team, Invite

class InviteFormTestCase(TestCase):
    """Unit tests of the invite form."""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
    ]

    def setUp(self):
        self.team = Team.objects.get(id=1)
        self.user = User.objects.get(username="@johndoe")
        self.other_user = User.objects.get(username="@janedoe")

        self.form_input = {
            "users_to_invite": [self.user, self.other_user],
            "invite_message": "Please join my team!",
        }

    def test_form_has_necessary_fields(self):
        form = InviteForm()
        self.assertIn('users_to_invite', form.fields)
        self.assertIn('invite_message', form.fields)
        users_to_invite_field = form.fields['users_to_invite']
        self.assertTrue(isinstance(users_to_invite_field, forms.CharField))
        self.assertTrue(isinstance(users_to_invite_field.widget, forms.Select))

    def test_valid_invite_form(self):
        form = InviteForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_must_invite_correctly(self):
        form = InviteForm(data=self.form_input)
        self.assertTrue(form.is_valid())
        before_count = Invite.objects.count()
        invite = form.send_invite(inviting_team=self.team)
        after_count = Invite.objects.count()
        self.assertEqual(after_count, before_count + 1)
        self.assertEqual(invite.inviting_team, self.team)
        self.assertEqual(invite.status, 'Reject')
        self.assertEqual(invite.invite_message, 'Please join my team!')
        self.assertTrue(self.user in invite.invited_users.all())
        self.assertTrue(self.other_user in invite.invited_users.all())
