"""Unit tests for the Teams model."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from tasks.models import User, Team

class TeamModelTestCase(TestCase):
    """Unit tests for the Team model."""

    
    fixtures = [
        'tasks/tests/fixtures/default_user.json',
        'tasks/tests/fixtures/other_users.json'
    ]

    def setUp(self):
        self.user = User.objects.get(username='@johndoe')
        self.other_user = User.objects.get(username="@peterpickles")
        self.team = Team.objects.create(
            team_name="Kangaroo",
            team_creator=self.user,
            description="The team we all wanted to be part of. Oh wait."
        )
        self.team.add_invited_member(self.user) # Add the creator to team
        self.team.add_invited_member(self.other_user)
        

    def test_valid_team(self):
        self._assert_team_is_valid()

    def test_team_name_cannot_be_blank(self):
        self.team.team_name = ''
        self._assert_team_is_invalid()

    def test_team_name_can_be_50_characters_long(self):
        self.team.team_name = 'x' * 50
        self._assert_team_is_valid()

    def test_team_name_cannot_be_over_50_characters_long(self):
        self.team.team_name = 'x' * 51
        self._assert_team_is_invalid()
    
    def test_team_description_can_be_blank(self):
        self.team.description = ''
        self._assert_team_is_valid()

    def test_team_description_can_be_200_characters_long(self):
        self.team.description = 'x' * 200
        self._assert_team_is_valid()

    def test_team_description_cannot_be_over_200_characters_long(self):
        self.team.description = 'x' * 201
        self._assert_team_is_invalid()

    def test_team_name_must_be_unique(self):
        second_team = Team.objects.create(
            team_name="FakeKangaroo",
            team_creator=self.other_user,
            description="Yep"
        )
        self.team.team_name = second_team.team_name
        self._assert_team_is_invalid()
    
    def test_team_must_have_a_creator(self):
        self.team.team_creator = None
        self._assert_team_is_invalid()
    
    def test_added_member_is_part_of_team(self):
        """Test that when a user is added to a team, they have been added properly"""

        second_user = User.objects.get(username='@janedoe')
        third_user = User.objects.get(username="@petrapickles")
        self.team.add_invited_member(second_user)
        self.team.add_invited_member(third_user)

        team_members = self.team.get_team_members().all()

        self.assertTrue(second_user in team_members and third_user in team_members)
    
    def test_each_team_member_is_part_of_team(self):
        """Test that when a user is added to a team, it is part of their team set"""

        second_user = User.objects.get(username='@janedoe')
        third_user = User.objects.get(username="@petrapickles")
        self.team.add_invited_member(second_user)
        self.team.add_invited_member(third_user)

        second_user_teams = second_user.get_teams()
        third_user_teams = third_user.get_teams()

        self.assertTrue(self.team in second_user_teams and self.team in third_user_teams)
    
    def test_remove_team_member(self):
        self.team.remove_team_member(self.other_user)
        team_members = self.team.get_team_members()

        self.assertTrue(self.other_user not in team_members)

    def _assert_team_is_valid(self):
        try:
            self.team.full_clean()
        except ValidationError:
            self.fail('Test team should be valid!')

    def _assert_team_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.team.full_clean()

