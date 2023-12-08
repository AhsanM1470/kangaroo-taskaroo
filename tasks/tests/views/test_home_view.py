"""Tests of the home view."""
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team

class HomeViewTestCase(TestCase):
    """Tests of the home view."""

    fixtures = ['tasks/tests/fixtures/default_user.json']

    def setUp(self):
        self.url = reverse('home')
        self.user = User.objects.get(username='@johndoe')
        team = Team.objects.create(
            team_name="My Team",
            team_creator=self.user,
            description="A default team for you to start managing your tasks!"
        )
        team.add_invited_member(self.user)


    def test_home_url(self):
        self.assertEqual(self.url,'/')

    def test_get_home(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_get_home_redirects_when_logged_in(self):
        self.client.login(username=self.user.username, password="Password123")
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')