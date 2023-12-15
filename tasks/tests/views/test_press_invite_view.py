from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Team, User, Invite
from urllib.parse import unquote

class PressInviteViewTestCase(TestCase, LogInTester):
    """Tests for the press invite view."""
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
    ]
    
    def setUp(self):
        self.user = User.objects.get(username='@janedoe')
        self.team = Team.objects.get(pk=1)
        self.other_team = Team.objects.create(
            team_name="Kangaroo",
            team_creator=self.user,
            description="The team we all wanted to be part of. Oh wait.",
        )
        self.other_team.add_invited_member(self.user)
        self.invite = Invite.objects.create(
            invite_message= "A random invite message",
            inviting_team = self.team
        )
        self.invite.set_invited_users("@janedoe")
        self.url = reverse('press_invite')
        self.client.login(username=self.user.username, password='Password123')

        self.form_input = {
            "status": "Reject",
            "id" : 1
        }

        session = self.client.session
        session["current_team_id"] = self.other_team.id
        session.save()

    def test_press_invite_url(self):
        self.assertEqual(unquote(self.url),f'/press_invite/')

    def test_get_press_invite_view(self):
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse('dashboard')
        self.assertRedirects(self.client.get(self.url), redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_accept_press_invite(self):
        self.form_input["status"] = "Accept"
        before_count = Invite.objects.count()
        response = self.client.post(self.url, follow=True, data=self.form_input)
        after_count = Invite.objects.count()
        self.assertEqual(after_count, before_count - 1)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')

        # Check if user has joined team
        self.assertTrue(self.user in self.team.get_team_members())

    def test_reject_press_invite(self):
        self.invite.status = "Reject"
        before_count = Invite.objects.count()
        response = self.client.post(self.url, follow=True, data=self.form_input)
        after_count = Invite.objects.count()
        self.assertEqual(after_count, before_count - 1)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertFalse(self.user in self.team.get_team_members())
        
