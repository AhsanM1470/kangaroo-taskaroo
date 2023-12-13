from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse, resolve
from tasks.models import Task, Team, User, Lane
from datetime import datetime
from tasks.forms import TaskForm
from django.contrib.auth import get_user_model
from tasks import views

class DashboardViewTestCase(TestCase, LogInTester):
    """Tests of the dashboard form view."""
    def setUp(self):
        self.user = User.objects.create_user(username='@johndoe', password='Password123')
        self.url = reverse('dashboard')
                           
        self.team1 = Team.objects.create(team_name="Team1", team_creator=self.user)
        self.team2 = Team.objects.create(team_name="Team2", team_creator=self.user)
        
        self.lane1 = Lane.objects.create(
            lane_name = "New Lane",
            lane_order = 1,
            team = self.team1
        )

        self.lane2 = Lane.objects.create(
            lane_name = "New Lane",
            lane_order = 2,
            team = self.team1
        )

        self.task1 = Task.objects.create(
            name='Task1',
            description='task',
            due_date=datetime(2025, 1, 19, 10, 5),
            lane = self.lane1,
            assigned_team = self.team1
        )

        self.task2 = Task.objects.create(
            name='Task2',
            description='task',
            due_date=datetime(2025, 1, 19, 10, 5),
            lane = self.lane2,
            assigned_team = self.team2
        )
        
        self.client.login(username='@johndoe', password='Password123')
        session = self.client.session
        session['current_team_id'] = self.team1.id
        session.save()

    # test if user is successfuly logged in
    def test_login_user(self):
        logged_in = self.client.login(username='@johndoe', password='Password123')
        self.assertTrue(logged_in)

    # test if the url is at the dashboard
    def test_dashboard_url(self):
        self.assertEqual(self.url, '/dashboard/')
    
    # test if 3 default lanes are made when a new team is created and there are no lanes
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
    
    # test adding a lane to the dashboard
    def test_add_lane(self):
        before_count = Lane.objects.count()
        response = self.client.post(reverse('dashboard'), {'add_lane': ''})
        self.assertEqual(response.status_code, 302)  
        self.assertTrue(Lane.objects.count() == before_count + 1)  # Check if lane was created

    # test renaming a lane
    def test_rename_lane(self):
        response = self.client.post(self.url, {
            'rename_lane': self.lane1.lane_id,
            'new_lane_name': 'New Name'
        })
        self.assertEqual(response.status_code, 302)
        self.lane1.refresh_from_db()
        self.assertEqual(self.lane1.lane_name, 'New Name')

    # test moving a task to the left lane (lane2 to lane 1)
    def test_move_task_left(self):
        response = self.client.post(self.url, {'move_task_left': self.task2.pk})
        self.assertEqual(response.status_code, 302)
        self.task2.refresh_from_db()
        self.assertEqual(self.task2.lane, self.lane1)
    
    # attempting to move a task to the left lane when there are no left lanes left
    # keeps the task in the current lane
    def test_move_task_left_out_of_bounds(self):
        response = self.client.post(self.url, {'move_task_left': self.task1.pk})
        self.assertEqual(response.status_code, 302)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.lane, self.lane1)

    # test moving a task to the right lane (lane1 to lane2)
    def test_move_task_right(self):
        response = self.client.post(self.url, {'move_task_right': self.task1.pk})
        self.assertEqual(response.status_code, 302)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.lane, self.lane2)

    # attempting to move a task to the right lane when there are no right lanes left
    # keeps the task in the current lane
    def test_move_task_right_out_of_bounds(self):
        response = self.client.post(self.url, {'move_task_right': self.task2.pk})
        self.assertEqual(response.status_code, 302)
        self.task2.refresh_from_db()
        self.assertEqual(self.task2.lane, self.lane2)

    # test moving a lane to the left, so that it is before the lane to the left of it
    def test_move_lane_left(self):
        response = self.client.post(self.url, {'move_lane_left': self.lane2.lane_id})
        self.assertEqual(response.status_code, 302) 
        self.lane1.refresh_from_db()
        self.lane2.refresh_from_db()
        self.assertEqual(self.lane2.lane_order, 1) # lane2 should now be at position 1
        self.assertEqual(self.lane1.lane_order, 2) # lane1 should now be at position 2

    # move a lane to the left when there is no lane to the left of it
    # keeps the lane in its current position
    def test_move_lane_left_out_of_bounds(self):
        response = self.client.post(self.url, {'move_lane_left': self.lane1.lane_id})
        self.assertEqual(response.status_code, 302) 
        self.lane1.refresh_from_db()
        self.lane2.refresh_from_db()
        self.assertEqual(self.lane1.lane_order, 1)
        self.assertEqual(self.lane2.lane_order, 2)
    
    # test moving a lane to the right, so that it is after the lane to the right of it
    def test_move_lane_right(self):
        response = self.client.post(self.url, {'move_lane_right': self.lane1.lane_id})
        self.assertEqual(response.status_code, 302) 
        self.lane1.refresh_from_db()
        self.lane2.refresh_from_db()
        self.assertEqual(self.lane1.lane_order, 2) # lane1 should now be at position 2
        self.assertEqual(self.lane2.lane_order, 1) # lane2 should now be at position 1

    # move a lane to the right when there is no lane to the right of it
    # keeps the lane in its current position
    def test_move_lane_left_out_of_bounds(self):
        response = self.client.post(self.url, {'move_lane_right': self.lane2.lane_id})
        self.assertEqual(response.status_code, 302) 
        self.lane1.refresh_from_db()
        self.lane2.refresh_from_db()
        self.assertEqual(self.lane1.lane_order, 1)
        self.assertEqual(self.lane2.lane_order, 2)