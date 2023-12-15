from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import Task, User, Lane, Team, Notification
from django.contrib.auth import get_user_model

class NotifDeleteViewTestCase(TestCase):
    """Tests for notif_delete view function"""
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json',
        'tasks/tests/fixtures/default_team.json',
    ]

    def setUp(self):
        self.user = User.objects.get(username="@johndoe")
        self.notification = Notification.objects.create()
        self.user.add_notification(self.notification)
        self.url = reverse('notif_delete',kwargs={'notif_id':self.user.get_notifications()[0].id})
        self.client.login(username=self.user.username, password='Password123')

    def test_notif_delete_url(self):
        self.assertEqual(self.url,'/notif_delete/1/')

    def test_successful_notif_delete(self):
        total_notifs_before = Notification.objects.count()
        user_notifs_before = self.user.notifications.count()
        response = self.client.post(self.url,follow=True)
        total_notifs_after = Notification.objects.count()
        user_notifs_after = self.user.notifications.count()
        self.assertEqual(total_notifs_after,total_notifs_before-1)
        self.assertEqual(user_notifs_after,user_notifs_before-1)
        redirect_url = reverse('dashboard')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'dashboard.html')





