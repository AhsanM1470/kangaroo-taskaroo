from django.core.management.base import BaseCommand, CommandError

from tasks.models import User, Team

import pytz
from faker import Faker
from random import randint, random

user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe'},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson'},
]


class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 300
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()
        self.users = User.objects.all()
        self.teams = Team.objects.all()

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        user_count = User.objects.count()
        while  user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end='\r')
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        user = self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name})
        if user is not None:
            print("waosaos")
            self.try_create_team(user)
       
    def try_create_user(self, data):
        try:
            user = self.create_user(data)
            return user
        except:
            pass
    
    def try_create_team(self, user):
        """Create a starting team for every user"""
        try:
            self.create_team(user)
        except:
            print("f me")
            pass

    def create_user(self, data):
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        return user 
    
    def create_team(self, user):
        team = Team.objects.create(
            team_name="My Team",
            team_creator=user,
            description="A default team for you to start managing your tasks!"
        )
        team.add_invited_member(user)
        team.save()
        print("sdsdo")


def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'
