from django.core.management.base import BaseCommand, CommandError

from tasks.models import User, Team, Task, Lane

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

    USER_COUNT = 10
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()
        self.users = User.objects.all()
        self.teams = Team.objects.all()
        self.create_shared_team()

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
        self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name})
       
    def try_create_user(self, data):
        try:
            if data['username'] == '@johndoe':
                user = self.create_superuser(data)
            else:
                user = self.create_user(data)
                if user is not None:
                    self.try_create_team(user)
        except:
            pass
    
    def try_create_team(self, user):
        """Create a starting team for every user"""
        try:
            self.create_team(user)
        except Exception as e:
            print(f"Error creating team for user {user.username}: {e}")

    def create_user(self, data):
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        return user 
  
    def create_superuser(self, data):
        user = User.objects.create_superuser(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
            is_superuser=True,
            is_staff=True,
        )
            
    def create_team(self, user):
        team = Team.objects.create(
            team_name="My Team",
            team_creator=user,
            description="A default team for you to start managing your tasks!"
        )
        team.add_invited_member(user)
        team.save()
        user.save()
        
    def create_shared_team(self):
        """Create a shared team for specified users."""
        try:
            shared_team = Team.objects.create(
                team_name="Shared Team",
                team_creator=User.objects.get(username='@johndoe'),
                description="A shared team for John, Jane, and Charlie."
            )
            for username in ['@johndoe', '@janedoe', '@charlie']:
                user = User.objects.get(username=username)
                shared_team.add_invited_member(user)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating shared team: {e}'))
            
    def create_tasks_for_user(self, user, team):
        task_name = self.faker.sentence()
        num_assigned_users = random.randint(1, min(5, self.USER_COUNT))  # Assign up to 5 users to a task
        assigned_users = random.sample(list(team.get_team_members), num_assigned_users)
        task = Task.objects.create(name=task_name, team=team)
        task.set_assigned_users(assigned_users)
        task.save()
        return task


def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'

