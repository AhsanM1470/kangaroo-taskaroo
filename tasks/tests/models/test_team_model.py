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
        self.team = Team.objects.create(
            team_name="Kangaroo",
            description="The team we all wanted to be part of. Oh wait."
        )
        self.user = User.objects.get(username='@johndoe')
        self.team.add_creator(self.user)

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
        self._assert_user_is_valid()

    def test_team_description_can_be_200_characters_long(self):
        self.team.description = 'x' * 200
        self._assert_team_is_valid()

    def test_team_description_cannot_be_over_200_characters_long(self):
        self.team.description = 'x' * 201
        self._assert_team_is_invalid()

    def test_team_name_must_be_unique(self):
        second_team = Team.objects.create(
            team_name="FakeKangaroo",
            description="Yep"
        )
        self.team.team_name = second_team.team_name
        self._assert_team_is_invalid()
    
    """
    Put this back in after

    def test_team_must_have_at_a_creator(self):
        self.team.team_creator = None
        self._assert_team_is_invalid()
    """

    def test_added_member_is_part_of_team(self):
        """Test that when a user is added to a team, """

        second_user = User.objects.get(username='@janedoe')
        third_user = User.objects.get(username="@petrapickles")
        self.team.add_invited_member(second_user)
        self.team.add_invited_member(third_user)

        team_members = self.get_team_members()

        self.assertTrue(second_user in team_members and third_user in team_members)
    
    def test_each_team_member_is_part_of_team(self):
        """Test that when a user is added to a team, """

        second_user = User.objects.get(username='@janedoe')
        third_user = User.objects.get(username="@petrapickles")
        self.team.add_invited_member(second_user)
        self.team.add_invited_member(third_user)

        second_user_teams = second_user.get_teams()
        third_user_teams = third_user.get_teams()

        self.assertTrue(self.team in second_user_teams and self.team in third_user_teams)

    def _assert_team_is_valid(self):
        try:
            self.team.full_clean()
        except ValidationError:
            self.fail('Test team should be valid!')

    def _assert_team_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.team.full_clean()


class Team(models.Model):
    """Model used to hold teams of different users and their relevant information"""
    
    team_name = models.CharField(max_length=50, unique=True, blank=False)
    team_members = models.ManyToManyField(User, blank=True)
    description = models.TextField(max_length=200, blank=True)
    
    def __str__(self):
        """Overrides string to show the team's name"""
        
        return self.team_name


    def add_creator(self, user):
        """Add the creator of the team to the team"""
        
        # May have administrator rights or something
        self.team_members.add(user)
        self.save()

    def add_team_member(self, new_team_members):
        """Add new team member/s to the team"""
        
        for new_team_member in new_team_members.all():
            self.team_members.add(new_team_member)
            self.save()
        
    def add_invited_member(self, user):
        """Add a new team member from an invite"""

        self.team_members.add(user)
        self.save()
    
    def remove_team_member(self, users_to_remove):
        """Removes user/s from team"""

        # Maybe use a query set for this too
        for user in users_to_remove:
            self.team_members.remove(user)
            self.save()
    
    def get_team_members(self):
        """Returns query set containing all the users in team"""

        return self.team_members.all()

    def get_team_members_list(self):
        """Return a string which shows the list of all the users in team"""

        output_str = ""
        users = self.get_team_members()

        for user in users:
            output_str += f'{user.username} '
        return output_str