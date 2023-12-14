from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Team, User
from tasks.forms import DeleteTeamForm
from urllib.parse import unquote

class DeleteTeamViewTestCase(TestCase, LogInTester):
    """Tests of the delete team view."""
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
    ]
    
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.other_user = User.objects.get(username="@janedoe")
        self.team = Team.objects.create(
            team_name = 'TestTeam',
            team_creator=self.user,
            description = "A random test team"
        )
        self.team.add_invited_member(self.user)
        self.team.add_invited_member(self.other_user)
        self.other_team = Team.objects.create(
            team_name = 'TestTeam2',
            team_creator=self.user,
            description = "A random test team"
        )
        self.other_team.add_invited_member(self.user)

        self.url = reverse('delete_team', kwargs={'team_id': self.team.id})

        self.form_input = {
            'confirm_deletion': True
        }
        
        self.client.login(username=self.user.username, password='Password123')

    def test_delete_team_url(self):
        self.assertEqual(unquote(self.url), f'/delete_team/1/')

    def test_get_delete_team_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delete_team.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, DeleteTeamForm))
        self.assertFalse(form.is_bound)
    
    def test_successful_team_delete(self):
        before_count = Team.objects.count()
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = Team.objects.count()
        self.assertEqual(after_count, before_count - 1)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        deleted_team = Team.objects.filter(team_name='TestTeam').first()
        self.assertIsNone(deleted_team, "Test Team should be deleted")

        # Check if every user in team doesn't belong to that team anymore
        self.assertTrue(self.team not in self.user.get_teams())
        self.assertTrue(self.team not in self.other_user.get_teams())
        
    def test_unsuccessful_team_delete(self):
        self.bad_form_input = { }
        before_count = Team.objects.count()
        response = self.client.post(self.url, self.bad_form_input)
        after_count = Team.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'delete_team.html')
        form = response.context['delete_form']
        self.assertTrue(isinstance(form, DeleteTeamForm))
        self.assertTrue(form.is_bound)
        self.assertTrue(Team.objects.filter(team_name='TestTeam').exists())