from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse, resolve
from tasks.models import Task, Team, User, Lane
from datetime import datetime, timezone
from tasks.forms import TaskForm
from django.contrib.auth import get_user_model
from tasks import views
import pytz

class DashboardViewTestCase(TestCase, LogInTester):
    """Tests of the dashboard form view."""
    
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
        'tasks/tests/fixtures/default_lane.json',
        'tasks/tests/fixtures/other_lanes.json',
        'tasks/tests/fixtures/default_task.json',
        'tasks/tests/fixtures/other_tasks.json'
    ]
    
    def setUp(self):
        self.url = reverse('dashboard')
        
        self.user = User.objects.get(username='@johndoe')
        
        self.task = Task.objects.get(pk=1) 
        self.task2 = Task.objects.get(pk=2) 
        self.lane = Lane.objects.get(pk=1)
        self.lane2 = Lane.objects.get(pk=2)
        self.team = Team.objects.get(pk=1)
        
        self.team2 = Team.objects.create(team_name="Team2", team_creator=self.user)
        
        self.client.login(username='@johndoe', password='Password123')
        session = self.client.session
        session['current_team_id'] = self.team.id
        session.save()

    # Test if user is successfuly logged in
    def test_login_user(self):
        logged_in = self.client.login(username='@johndoe', password='Password123')
        self.assertTrue(logged_in)

    # Test if the url is at the dashboard
    def test_dashboard_url(self):
        self.assertEqual(self.url, '/dashboard/')
    
    # Test if 3 default lanes are made when a new team is created and there are no lanes
    def test_dashboard_with_no_lanes(self):
        self.team = Team.objects.create(team_name="Test Team", team_creator=self.user) # team with no lanes
        session = self.client.session
        session['current_team_id'] = self.team.id
        session.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        lanes = Lane.objects.filter(team=self.team)

        self.assertEqual(lanes.count(), 3)

        default_lanes = [("Backlog", 1), ("In Progress", 2), ("Complete", 3)]
        for lane_name, lane_order in default_lanes:
            lane = lanes.get(lane_name = lane_name)
            self.assertEqual(lane.lane_order, lane_order)
    
    # Test adding a lane to the dashboard
    def test_add_lane(self):
        before_count = Lane.objects.count()
        response = self.client.post(reverse('dashboard'), {'add_lane': ''})
        self.assertEqual(response.status_code, 302)  
        self.assertTrue(Lane.objects.count() == before_count + 1)  # Check if lane was created

    # Test renaming a lane
    def test_rename_lane(self):
        response = self.client.post(self.url, {
            'rename_lane': self.lane.lane_id,
            'new_lane_name': 'New Name'
        })
        self.assertEqual(response.status_code, 302)
        self.lane.refresh_from_db()
        self.assertEqual(self.lane.lane_name, 'New Name')

    # Test moving a task to the left lane (lane2 to lane 1)
    def test_move_task_left(self):
        response = self.client.post(self.url, {'move_task_left': self.task2.pk})
        self.assertEqual(response.status_code, 302)
        self.task2.refresh_from_db()
        self.assertEqual(self.task2.lane, self.lane)
    
    # Attempting to move a task to the left lane when there are no left lanes left
    # Keeps the task in the current lane
    def test_move_task_left_out_of_bounds(self):
        response = self.client.post(self.url, {'move_task_left': self.task.pk})
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.lane, self.lane)

    # Test moving a task to the right lane (lane to lane2)
    def test_move_task_right(self):
        response = self.client.post(self.url, {'move_task_right': self.task.pk})
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.lane, self.lane2)

    # Attempting to move a task to the right lane when there are no right lanes left
    # Keeps the task in the current lane
    def test_move_task_right_out_of_bounds(self):
        response = self.client.post(self.url, {'move_task_right': self.task2.pk})
        self.assertEqual(response.status_code, 302)
        self.task2.refresh_from_db()
        self.assertEqual(self.task2.lane, self.lane2)

    # Test moving a lane to the left, so that it is before the lane to the left of it
    def test_move_lane_left(self):
        response = self.client.post(self.url, {'move_lane_left': self.lane2.lane_id})
        self.assertEqual(response.status_code, 302) 
        self.lane.refresh_from_db()
        self.lane2.refresh_from_db()
        self.assertEqual(self.lane2.lane_order, 1) # lane2 should now be at position 1
        self.assertEqual(self.lane.lane_order, 2) # lane should now be at position 2

    # Move a lane to the left when there is no lane to the left of it
    # Keeps the lane in its current position
    def test_move_lane_left_out_of_bounds(self):
        response = self.client.post(self.url, {'move_lane_left': self.lane.lane_id})
        self.assertEqual(response.status_code, 302) 
        self.lane.refresh_from_db()
        self.lane2.refresh_from_db()
        self.assertEqual(self.lane.lane_order, 1)
        self.assertEqual(self.lane2.lane_order, 2)
    
    # Test moving a lane to the right, so that it is after the lane to the right of it
    def test_move_lane_right(self):
        response = self.client.post(self.url, {'move_lane_right': self.lane.lane_id})
        self.assertEqual(response.status_code, 302) 
        self.lane.refresh_from_db()
        self.lane2.refresh_from_db()
        self.assertEqual(self.lane.lane_order, 2) # lane should now be at position 2
        self.assertEqual(self.lane2.lane_order, 1) # lane2 should now be at position 1

    # Move a lane to the right when there is no lane to the right of it
    # Keeps the lane in its current position
    def test_move_lane_left_out_of_bounds(self):
        response = self.client.post(self.url, {'move_lane_right': self.lane2.lane_id})
        self.assertEqual(response.status_code, 302) 
        self.lane.refresh_from_db()
        self.lane2.refresh_from_db()
        self.assertEqual(self.lane.lane_order, 1)
        self.assertEqual(self.lane2.lane_order, 2)