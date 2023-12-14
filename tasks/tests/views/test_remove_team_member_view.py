from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Team, User
from tasks.forms import RemoveMemberForm
from urllib.parse import unquote

class RemoveTeamMemberViewTestCase(TestCase, LogInTester):
    """Tests for the remove team member view."""
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

        self.url = reverse('remove_member', kwargs={'member_id': self.other_user.id})

        self.form_input = {
            'confirm_deletion': True
        }

        self.client.login(username=self.user.username, password='Password123')
        session = self.client.session
        session["current_team_id"] = self.team.id
        session.save()

    def test_remove_member_url(self):
        self.assertEqual(unquote(self.url), f'/remove_member/2/')

    def test_get_delete_team_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'remove_team_member.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, RemoveMemberForm))
        self.assertFalse(form.is_bound)
    
    def test_successful_remove_member(self):
        before_count = self.team.get_team_members().count()
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = self.team.get_team_members().count()
        self.assertEqual(after_count, before_count - 1)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        removed_user = self.team.get_team_members().filter(username=self.other_user.username).first()
        self.assertIsNone(removed_user, "User should not be in team anymore!")

        # Check if user doesn't belong to that team anymore
        self.assertTrue(self.team not in self.other_user.get_teams())
        
    def test_unsuccessful_remove_team_member(self):
        self.bad_form_input = { }
        before_count = self.team.get_team_members().count()
        response = self.client.post(self.url, data=self.bad_form_input)
        after_count = self.team.get_team_members().count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'remove_team_member.html')
        form = response.context['remove_member_form']
        self.assertTrue(isinstance(form, RemoveMemberForm))
        self.assertTrue(self.team in self.other_user.get_teams())