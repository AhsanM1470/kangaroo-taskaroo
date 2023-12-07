from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import TaskNotification, InviteNotification,Task,Team,Invite,User
import datetime

class TaskNotificationModelTestCase(TestCase):
    """Testing for the TaskNotification model"""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]

    def setUp(self):
        
        self.user = User.objects.get(username='@johndoe')
        self.task = Task.objects.create(
            name = 'test-task',
            description = 'A random test task',
            due_date = datetime.datetime(2023, 11, 28, 10, 0),
        )
        self.assign_notification = TaskNotification.objects.create(task=self.task,notification_type="AS")
        self.deadline_notification = TaskNotification.objects.create(task=self.task,notification_type="DL")
        self.user.add_notification(self.assign_notification)
        self.user.add_notification(self.deadline_notification)
        self.task_notifs = self.user.notifications.select_related("tasknotification")

    def test_correct_task_name(self):
        self.assertEqual(self.assign_notification.task.name,"test-task")
        self.assertEqual(self.deadline_notification.task.name,"test-task")

    def test_assignment_notification_displays_correctly(self):
        display_result = self.assign_notification.display()
        target = "test-task has been assigned to you."
        self.assertEquals(display_result,target)

    def test_deadline_notification_displays_correctly(self):
        display_result = self.deadline_notification.display()
        target = "test-task's deadline is approaching."
        self.assertEqual(display_result,target)

    def test_notifications_stored_correctly(self):
        self.assertEqual(self.task_notifs.count(),2)
        for notif in self.task_notifs:
            self.assertIsInstance(notif.tasknotification,TaskNotification)


class InviteNotificationModelTestCase(TestCase):
    """Testing for the InviteNotification model"""

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
