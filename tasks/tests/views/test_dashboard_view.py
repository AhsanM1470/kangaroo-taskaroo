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
                           
        self.team = Team.objects.create(
            team_name="Team1",
            team_creator=self.user,
            description="team"
        )

        self.team2 = Team.objects.create(
            team_name="Team2",
            team_creator=self.user,
            description="team"
        )
        
        self.lane = Lane.objects.create(
            lane_name = "New Lane",
            lane_order = 1,
            team = self.team1
        )

        self.lane2 = Lane.objects.create(
            lane_name = "New Lane",
            lane_order = 2,
            team = self.team1
        )

        self.task = Task.objects.create(
            name='Task1',
            description='task',
            due_date=datetime(2025, 1, 19, 10, 5),
            lane = self.lane,
            assigned_team = self.team
        )
        self.task2 = Task.objects.create(
            name='Task 2',
            description='task',
            due_date=datetime(2025, 1, 19, 10, 5),
            lane = self.lane,
            assigned_team = self.team
        )
        
        self.client.login(username='@johndoe', password='Password123')
        self.client.session['current_team_id'] = self.team.id
        self.session.save()

    def test_login_user(self):
        # Log in the user using the test client
        logged_in = self.client.login(username='@johndoe', password='Password123')

        # Check if login was successful
        self.assertTrue(logged_in)

    # Test URLs

    def test_dashboard_url(self):
        self.assertEqual(self.url, '/dashboard/')
        # url = reverse('dashboard')
        # self.assertEqual(resolve(url).func, views.dashboard)

    # def test_move_lane_left_url(self):
    #     self.assertEqual(self.url, f'/move_lane_left/{self.lane.lane_id}/')
    
    # def test_move_lane_right_url(self):
    #     self.assertEqual(self.url, f'/move_lane_left/{self.lane.lane_id}/')

    # def test_move_task_left_url(self):
    #     self.assertEqual(self.url, f'/move_lane_left/{self.task.pk}/')

    # def test_move_task_right_url(self):
    #     self.assertEqual(self.url, f'/move_lane_left/{self.task.pk}/')

    # def test_add_lane(self):
    #     before_count = Lane.objects.count()
    #     response = self.client.post(self.url, {'add_lane': True})
    #     self.assertEqual(response.status_code, 200)


    # def test_successful_task_create(self):
    #     before_count = Task.objects.count()
    #     response = self.client.post(self.url, data=self.form_input, follow=True)
    #     after_count = Task.objects.count()
    #     self.assertEqual(after_count, before_count + 1)
    #     redirect_url = reverse('dashboard')
    #     self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
    #     self.assertTemplateUsed(response, 'dashboard.html')
    #     created_task = Task.objects.filter(name='SpecialTask').first()
    #     self.assertIsNotNone(created_task, "SpecialTask should be created")
    #     self.assertEqual(created_task.description, 'Amys special task within task manager!')
        
    # def test_unsuccesful_task_create(self):
    #     self.task_data_bad = {
    #         'name': 'Ta',
    #         'description': 'Amys fifth task within task manager!',
    #         'due_date': '2023-12-19 15:30',
    #     }
    #     before_count = Task.objects.count()
    #     response = self.client.post(self.url, self.task_data_bad)
    #     after_count = Task.objects.count()
    #     self.assertEqual(after_count, before_count)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'task_create.html')
    #     form = response.context['form']
    #     self.assertTrue(isinstance(form, TaskForm))
    #     self.assertTrue(form.is_bound)
    #     self.assertFalse(Task.objects.filter(name='Ta').exists())
    
    def test_add_lane(self):
        before_count = Lane.objects.count()
        response = self.client.post(reverse('dashboard'), {'add_lane': ''})
        self.assertEqual(response.status_code, 302)  # Redirect status
        self.assertTrue(Lane.objects.count() == before_count + 1)  # Check if lane was created

    def test_rename_lane(self):
        response = self.client.post(reverse('dashboard'), {
            'rename_lane': self.lane.lane_id,
            'new_lane_name': 'New Name'
        })
        self.assertEqual(response.status_code, 302)  # Redirect status
        self.lane.refresh_from_db()
        self.assertEqual(self.lane.lane_name, 'New Name')