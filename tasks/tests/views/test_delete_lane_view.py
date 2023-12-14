from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Lane, Team
from datetime import datetime, date, time
from tasks.forms import LaneDeleteForm
from django.contrib.auth import get_user_model


class TaskEditViewTestCase(TestCase, LogInTester):
    """Tests of the delete lane view."""

    def setUp(self):
        self.user = User.objects.create_user(username='@johndoe', password='Password123')

        self.team = Team.objects.create(team_name="Team1", team_creator=self.user)

        self.lane = Lane.objects.create(
            lane_name = "New Lane",
            lane_order = 1,
            team = self.team
        )

        self.form_input = {
            'confirm_deletion': True
        }

        self.url = reverse('lane_delete', kwargs={'lane_id': self.lane.lane_id})
        self.client.login(username=self.user.username, password='Password123')

    # Test if user is successfuly logged in
    def test_login_user(self):
        logged_in = self.client.login(username='@johndoe', password='Password123')
        self.assertTrue(logged_in)

    # Test URL
    def test_delete_lane_url(self):
        self.assertEqual(self.url, f'/lane_delete/{self.lane.lane_id}/')

    # Test getting the lane to delete
    def test_get_lane(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lane_delete.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, LaneDeleteForm))
        self.assertFalse(form.is_bound)
    
    # Test lane deletion
    def test_successful_lanes_delete(self):
        session = self.client.session
        session['current_team_id'] = self.team.pk
        session.save()

        self.lane2 = Lane.objects.create(
            lane_name = "New Lane",
            lane_order = 2,
            team = self.team
        )

        before_count = Lane.objects.count()
        self.assertEqual(before_count, 2) # 2 lanes in the team
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = Lane.objects.count()
        self.assertEqual(after_count, before_count - 1) # lane deleted
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')

    # Test if the 3 default lanes are recreated when there are no lanes remaining after deletion
    def test_successful_lanes_delete_when_no_lanes(self):
        session = self.client.session
        session['current_team_id'] = self.team.pk
        session.save()
        before_count = Lane.objects.count()
        self.assertEqual(before_count, 1) # 1 lane in the team
        response = self.client.post(self.url, data=self.form_input, follow=True)
        after_count = Lane.objects.count()
        self.assertEqual(after_count, 3) # when there are no lanes, the 3 default lanes should be remade
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')
