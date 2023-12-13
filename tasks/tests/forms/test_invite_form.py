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
        self.user = User.objects.get(username="@janedoe")
        self.form_input = {
            "team_name": "Kangaroo",
            "description": "The team we all wanted to be part of. Oh wait.",
            "members_to_invite": "@janedoe"
        }

    def test_form_has_necessary_fields(self):
        form = InviteForm()
        ['team_name', 'description', 'members_to_invite']
        self.assertIn('team_name', form.fields)
        self.assertIn('description', form.fields)
        self.assertIn('members_to_invite', form.fields)
        members_to_invite_field = form.fields['members_to_invite']
        self.assertTrue(isinstance(members_to_invite_field, forms.CharField))
        self.assertTrue(isinstance(members_to_invite_field.widget, forms.Select))

    def test_valid_invite_form(self):
        form = InviteForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_uses_model_validation(self):
        self.form_input['team_name'] = ""
        form = CreateTeamForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_must_save_correctly(self):
        user = User.objects.get(username='@johndoe')
        form = CreateTeamForm(data=self.form_input)
        self.assertTrue(form.is_valid())
        before_count = Team.objects.count()
        team = form.create_team(user)
        after_count = Team.objects.count()
        self.assertNotEqual(after_count, before_count)
        self.assertEqual(team.team_name, 'Kangaroo')
        self.assertEqual(team.description, 'The team we all wanted to be part of. Oh wait.')
        self.assertEqual(team.team_creator, user)
        self.assertTrue(user in team.get_team_members())

        # Check if invite has been created to the user we specified to invite
        invite = Invite.objects.all().first()
        self.assertTrue(isinstance(invite, Invite))
        self.assertTrue(self.user in invite.invited_users.all())
