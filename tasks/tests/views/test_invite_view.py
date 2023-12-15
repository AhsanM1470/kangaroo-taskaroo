from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Team, User, Invite
from tasks.forms import InviteForm
from urllib.parse import unquote

class InviteViewTestCase(TestCase, LogInTester):
    """Tests of the invite view."""
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_task.json',
        'tasks/tests/fixtures/default_lane.json'
    ]
    
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.get(id=1)
        self.form_input = {
            "users_to_invite": "@johndoe",
            "invite_message": "Please join my team!",
        }

        self.url = reverse('create_invite')
        self.client.login(username=self.user.username, password='Password123')

        session = self.client.session
        session["current_team_id"] = self.team.id
        session.save()

    def test_invite_url(self):
        self.assertEqual(unquote(self.url),f'/create_invite/')

    def test_get_invite_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invite.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, InviteForm))
        self.assertFalse(form.is_bound)

    def test_successful_create_invite(self):
        before_count = Invite.objects.count()
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = Invite.objects.count()
        self.assertEqual(after_count, before_count + 1)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')

        # Check if invite has been created to the user we specified to invite
        invite = Invite.objects.all().first()
        self.assertTrue(isinstance(invite, Invite))
        self.assertTrue(self.user in invite.invited_users.all())

    def test_unsuccessful_create_invite(self):
        bad_input = {
            "users_to_invite": "",
            "invite_message": "Please join my team!",
        }
        before_count = Invite.objects.count()
        response = self.client.post(self.url, data=bad_input, follow=True)
        after_count = Invite.objects.count()
        self.assertEqual(after_count, before_count)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertTrue(Invite.objects.all().first() is None)
        
