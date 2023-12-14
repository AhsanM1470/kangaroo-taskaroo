from tasks.tests.helpers import LogInTester
from django.test import TestCase
from django.urls import reverse
from tasks.models import User, Team
from django.contrib.auth import get_user_model


class SignalsViewCase(TestCase, LogInTester):
    """Tests of the task edit view."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            username = "@superuser1",
            email = "superuser1@example.com",
            first_name= "super",
            last_name = "user"
        )
        
        self.user2 = User.objects.create(
            username = "@superuser2",
            email = "superuser2@example.com",
            first_name= "super",
            last_name = "user"
        )

    def test_created_superuser_has_team(self):
        team = Team.objects.filter(team_creator=self.user.pk)
        self.assertIsNotNone(team)
        
    def test_new_superuser_has_team(self):
        self.user2.is_superuser = True
        self.user2.is_staff = True
        self.user2.save()
        
        team = Team.objects.get(team_creator=self.user2.pk)
        self.assertIsNotNone(team)






