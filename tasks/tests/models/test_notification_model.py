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
        self.creator = User.objects.get(username='@johndoe')
        self.team = Team.objects.create(
            team_name = 'test-team',
            team_creator= self.creator,
            description = "A random test team"
        )
        self.team.add_invited_member(self.creator)

        self.invitees = User.objects.filter(username='@janedoe')
        self.invitee = User.objects.get(username='@janedoe')
        self.invite = Invite.objects.create(
            invite_message= "A random invite message",
            inviting_team = self.team
        )

        self.invite.set_invited_users(self.invitees)
        self.notifications = self.invitee.get_notifications()
        self.invite_notifs = self.notifications.select_related("invitenotification")

    def test_correct_team_name(self):
        team = self.invite_notifs[0].invitenotification.invite.get_inviting_team()
        self.assertEqual(team.team_name,'test-team')

    def test_notification_displays_correctly(self):
        target = "Do you wish to join test-team?"
        display_result = self.invite_notifs[0].invitenotification.display()
        self.assertEqual(display_result,target)

    def test_notification_gets_stored(self):
        self.assertEqual(self.invite_notifs.count(),1)
        self.assertIsInstance(self.invite_notifs[0].invitenotification,InviteNotification)



        


    