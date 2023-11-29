from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import TaskNotification, InviteNotification,Task,Team,Invite,User
import datetime

class TaskNotificationModelTestCase(TestCase):
    """Testing for the TaskNotification model"""

    def setUp(self):
        self.task = Task.objects.create(
            name = 'test-task',
            description = 'A random test task',
            due_date = datetime.datetime(2023, 11, 28, 10, 0),
        )
        self.notification = TaskNotification()
        self.notification.task = self.task

    def test_correct_task_name(self):
        self.assertEqual(self.notification.task.name,"test-task")

    def test_assignment_notification_displays_correctly(self):
        display_result = self.notification.display("AS")
        target = "test-task has been assigned to you."
        self.assertEquals(display_result,target)

    def test_deadline_notification_displays_correctly(self):
        display_result = self.notification.display("DL")
        target = "test-task's deadline is approaching."
        self.assertEqual(display_result,target)

class InviteNotificationModelTestCase(TestCase):

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]
    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.create(
            team_name = 'test-team',
            description = "A random test team"
        )
        self.invite = Invite.objects.create(
            invite_message= "A random invite message"
        )
        self.invite.invited_users.add(self.user)
        self.invite.set_team(self.team)
        self.notification = InviteNotification()
        self.notification.invite = self.invite

    def test_correct_team_details(self):
        actualTeam = self.notification.invite.get_inviting_team()
        self.assertEqual(actualTeam, self.team)
        self.assertEqual(actualTeam.team_name, self.team.team_name)


    