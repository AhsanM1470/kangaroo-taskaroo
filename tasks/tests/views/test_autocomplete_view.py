from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Team, User, Invite
from django.http import HttpResponse, JsonResponse
from urllib.parse import unquote

class AutocompleteViewTestCase(TestCase, LogInTester):
    """Tests for the autocomplete view."""
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
        self.other_user = User.objects.get(username='@janedoe')
        self.team.add_invited_member(self.user)
        self.team.add_invited_member(self.other_user)
        self.form_input = {
            "q": "@petra",
        }

        self.url = reverse('autocomplete_user')
        self.client.login(username=self.user.username, password='Password123')

        session = self.client.session
        session["current_team_id"] = self.team.id
        session.save()

    def test_autocomplete_url(self):
        self.assertEqual(unquote(self.url),f'/autocomplete_user/')

    def test_get_autocomplete(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_successful_autocomplete_request(self):
        response = self.client.get(self.url, data=self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response, JsonResponse))
    
    def test_unsuccessful_autocomplete_request(self):
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response, HttpResponse))
        
    def test_autocomplete_does_not_show_self(self):
        response = self.client.get(self.url, data=self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response, JsonResponse))
        self.assertTrue(self.user.username not in str(response.content))
    
    def test_autocomplete_does_not_show_existing_team_members(self):
        response = self.client.get(self.url, data=self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response, JsonResponse))
        self.assertTrue(self.other_user.username not in str(response.content))
    
    def test_autocomplete_shows_correct_options(self):
        response = self.client.get(self.url, data=self.form_input, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response, JsonResponse))
        self.assertTrue("@petrapickles" in str(response.content))

