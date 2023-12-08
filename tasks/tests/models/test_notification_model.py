from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import TaskNotification, InviteNotification,Task,Team,Invite,User,Lane
from datetime import datetime,timedelta

class TaskNotificationModelTestCase(TestCase):
    """Testing for the TaskNotification model"""

    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]

    def setUp(self):
        
        self.user = User.objects.get(username='@johndoe')
        self.team = Team.objects.create(
            team_name = 'test-team',
            team_creator= self.user,
            description = "A random test team"
        )
        self.team.add_invited_member(self.user)
        self.lane = Lane.objects.create(
            lane_id = 1
        )
        self.task = Task.objects.create(
            name = 'test-task',
            description = 'A random test task',
            due_date = datetime.today()+timedelta(days=5),
            assigned_team=self.team,
            lane = self.lane
        )
        self.task.set_assigned_users(User.objects.filter(username="@johndoe"))
        self.task.notify_keydates()
        self.notifications = self.user.get_notifications()
        self.task_notifs = [notif.as_task_notif() for notif in self.notifications.select_related("tasknotification")]
        self.assign_notifications = list(filter(lambda notif: notif.notification_type==TaskNotification.NotificationType.ASSIGNMENT,self.task_notifs))
        self.deadline_notifications = list(filter(lambda notif: notif.notification_type==TaskNotification.NotificationType.DEADLINE,self.task_notifs))

    def test_correct_task_name(self):
        self.assertEqual(self.assign_notifications[0].task.name,"test-task")
        self.assertEqual(self.deadline_notifications[0].task.name,"test-task")

    def test_assignment_notification_displays_correctly(self):
        self.assertEqual(len(self.assign_notifications),1)
        display_result = self.assign_notifications[0].display()
        target = "test-task has been assigned to you."
        self.assertEquals(display_result,target)

    def test_deadline_notification_displays_correctly(self):
        self.assertEqual(len(self.deadline_notifications),1)
        display_result = self.deadline_notifications[0].display()
        target = "test-task's deadline is in 5 day(s)."
        self.assertEqual(display_result,target)

    def test_notifications_stored_correctly(self):
        self.assertEqual(self.notifications.count(),2)
        self.assertEqual(len(self.task_notifs),2)
        
        


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
        self.assertEqual(self.notifications.count(),1)
        self.assertEqual(self.invite_notifs.count(),1)
