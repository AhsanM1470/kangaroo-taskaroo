"""Unit tests for the Invite model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import User, Team, Invite

class InviteModelTestCase(TestCase):
    """Unit tests for the Invite model."""

    
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]

    def setUp(self):
        self.team = Team.objects.create(
            team_name="Kangaroo",
            description="The team we all wanted to be part of. Oh wait."
        )
        self.user = User.objects.get(username='@johndoe')
        self.other_user = User.objects.get(username="@peterpickles")
        self.team.add_creator(self.user)

        users_to_invite = User.objects.filter(username="@peterpickles") 
        
        self.invite = Invite.objects.create(
            invite_message="Yo Yo Yo",
            inviting_team=self.team
        )
        self.invite.set_invited_users(users_to_invite)
        

    def test_valid_invite(self):
        self._assert_invite_is_valid()

    def test_invite_must_invite_a_user(self):
        self.invite.invited_users.clear()
        self._assert_invite_is_invalid()
    
    def test_inviting_team_must_not_be_blank(self):
        self.invite.inviting_team = None
        self._assert_invite_is_invalid()

    def test_invite_message_can_be_100_characters_long(self):
        self.invite.invite_message = 'x' * 100
        self._assert_invite_is_valid()

    def test_invite_message_cannot_be_over_100_characters_long(self):
        self.invite.invite_message = 'x' * 101
        self._assert_invite_is_invalid()
    
    def test_accepted_invite_adds_members_to_team(self):
        """Check that users have been added to team from invite"""
        self.invite.status = "Accept"
        inviting_team = self.invite.inviting_team
        invited_users = self.invite.invited_users
        self.invite.close()

        for user in invited_users.all():
            self.assertTrue(inviting_team in user.get_teams())
    
    def test_closed_invite_is_deleted(self):
        id = self.invite.id
        self.invite.close()

        with self.assertRaises(Invite.DoesNotExist):
            Invite.objects.get(pk = id) 

    def _assert_invite_is_valid(self):
        try:
            self.invite.full_clean()
        except ValidationError:
            self.fail('Test Invite should be valid!')

    def _assert_invite_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.invite.full_clean()

