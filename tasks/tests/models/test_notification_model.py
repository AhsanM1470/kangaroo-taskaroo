from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import Notification

class NotificationModelTestCase(TestCase):
    def setUp(self):
        self.notification = Notification()
        self.notification.task_name = "test-task"

    def test_correct_task_name(self):
        self.assertEqual(self.notification.task_name,"test-task")

    def test_assignment_notification_displays_correctly(self):
        display_result = self.notification.display("AS")
        target = "test-task has been assigned to you."
        self.assertEquals(display_result,target)

    def test_deadline_notification_displays_correctly(self):
        display_result = self.notification.display("DL")
        target = "test-task's deadline is approaching."
        self.assertEquals(display_result,target)

    