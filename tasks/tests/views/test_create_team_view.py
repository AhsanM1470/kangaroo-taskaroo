from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Team, User, Invite
from tasks.forms import CreateTeamForm
from urllib.parse import unquote

class CreateTeamViewTestCase(TestCase, LogInTester):
    """Tests of the create team view."""
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_task.json',
        'tasks/tests/fixtures/default_lane.json'
    ]
    
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.other_user = User.objects.get(username='@janedoe')
        self.form_input = {
            "team_name": "Kangaroo",
            "description": "The team we all wanted to be part of. Oh wait.",
            "members_to_invite": "@janedoe"
        }

        self.url = reverse('create_team')
        self.client.login(username=self.user.username, password='Password123')

    def test_create_team_url(self):
        self.assertEqual(unquote(self.url),f'/create_team/')

    def test_get_create_team(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_team.html')
        form = response.context['team_form']
        self.assertTrue(isinstance(form, CreateTeamForm))
        self.assertFalse(form.is_bound)

    def test_successful_create_team(self):
        before_count = Team.objects.count()
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = Team.objects.count()
        self.assertEqual(after_count, before_count + 1)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        team = Team.objects.get(team_name="Kangaroo")
        self.assertEqual(team.team_name, 'Kangaroo')
        self.assertEqual(team.description, 'The team we all wanted to be part of. Oh wait.')
        self.assertEqual(team.team_creator, self.user)
        self.assertTrue(self.user in team.get_team_members())

        # Check if invite has been created to the user we specified to invite
        invite = Invite.objects.all().first()
        self.assertTrue(isinstance(invite, Invite))
        self.assertTrue(self.other_user in invite.invited_users.all())

    def test_unsuccessful_create_team(self):
        form_input = self.form_input
        form_input["team_name"] = ""
        before_count = Team.objects.count()
        response = self.client.post(self.url, data=form_input, follow=True)
        after_count = Team.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        form = response.context['team_form']
        self.assertTrue(isinstance(form, CreateTeamForm))
        self.assertTrue(form.is_bound)
        self.assertFalse(Team.objects.filter(team_name="Kangaroo").exists())
        
