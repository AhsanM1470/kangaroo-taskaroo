from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import timedelta
from django.utils import timezone
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

    USER_COUNT = 300
    TEAM_COUNT = 100
    MAX_USERS_PER_TEAM = 25
    MAX_LANES_PER_TEAM = 8
    MAX_TASKS_PER_LANE = 5

    
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):

        self.create_users()
        self.users = User.objects.all()
        self.create_shared_team()
        random_teams = self.generate_random_teams(self.users)
        self.generate_random_lanes(random_teams)

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
                    self.try_create_starter_team(user)
        except:
            pass
    
    def try_create_starter_team(self, user):
        """Create a starting team for every user"""
        try:
            self.create_default_team(user)
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
        return user
            
    def create_default_team(self, user):
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
            
# Random Team Generation

    def try_create_team(self):
        try:
            name = self.faker.word()
            name = name[:50]
            team_creator = self.faker.random_element(self.users)
            description=self.faker.paragraph()
            description = description[:200]
            team = Team.objects.create(
                team_name=name,
                description=description,
                team_creator=team_creator
            )
            team.add_invited_member(team_creator)
            return team
        except:
            return None

    def generate_random_teams(self, users):
        teams_count = 0
        teams = []
        while teams_count < self.TEAM_COUNT:
            print(f"Seeding team {teams_count}/{self.TEAM_COUNT}", end='\r')
            team = self.try_create_team()
            if team is not None:
                num_members = self.faker.pyint(min_value=1, max_value=self.MAX_USERS_PER_TEAM)
                random_users = self.faker.random_elements(list(users), num_members, unique=True)
                for user in random_users:
                    if user not in team.team_members.all():
                        team.team_members.add(user)
                team.save()
                teams.append(team)
                teams_count += 1
        print("Team seeding complete.      ")
        return teams
        
# Random Task Generation
        
    def generate_valid_lane_name(self, validator):
        while True:
            lane_name = self.faker.word()
            try:
                validator(lane_name) 
                return lane_name
            except ValidationError:
                pass
    
    def try_create_lane(self, order_number, team):
        alphanumeric = RegexValidator(
            regex=r'^[a-zA-Z0-9 ]{1,}$',
            message='Enter a valid word with at least 1 alphanumeric character (no special characters allowed).',
            code='invalid_lane_name'
        )
        
        try:
            name = self.generate_valid_lane_name(alphanumeric)
            name = name[:50]
            lane = Lane.objects.create(
                lane_name=name,
                lane_order=order_number,
                team=team
            )
            return lane
        except:
            return None
        
    def generate_random_lanes(self, teams):
        count = 0
        for team in teams:
            print(f"Seeding lanes and tasks for team {count}/{self.TEAM_COUNT}", end='\r')
            number_of_lanes = self.faker.pyint(min_value=1, max_value=self.MAX_LANES_PER_TEAM)
            lanes_count = 0
            while lanes_count < number_of_lanes:
                lane = self.try_create_lane(lanes_count, team)
                if lane is not None:
                    number_of_tasks = self.faker.pyint(min_value=1, max_value=self.MAX_TASKS_PER_LANE)
                    tasks = self.generate_random_tasks_for_lane(lane, number_of_tasks, team)
                    self.set_dependencies_for_tasks(tasks)
                    lanes_count += 1
            count += 1
        print("Lane seeding complete.      ")
        
# Random Task Generation
        
    def generate_valid_task_name(self, validator):
        while True:
            task_name = self.faker.word()
            try:
                validator(task_name) 
                return task_name
            except ValidationError:
                pass
        
    def try_create_task(self, lane, team):
        alphanumeric = RegexValidator(
        regex=r'^[a-zA-Z0-9 ]{3,}$',
        message='Enter a valid word with at least 3 alphanumeric characters (no special characters allowed).',
        code='invalid_word',
        )
        
        try:
            name = self.generate_valid_lane_name(alphanumeric)
            name = name[:30]
            description=self.faker.paragraph()
            description = description[:200]
            due_date = self.faker.date_time_this_decade(after_now=True, before_now=False, tzinfo=timezone.utc) + timedelta(days=100)
            task_priority = self.faker.random_element(['low', 'medium', 'high'])
            
            task = Task.objects.create(
                name=name,
                description = description,
                due_date = due_date,
                assigned_team=team,
                lane = lane,
                priority = task_priority
            )
            
            return task
        except:
            return None
        
    def generate_random_tasks_for_lane(self, lane, number_of_tasks, team):
        task_count = 0
        tasks = []
        while task_count < number_of_tasks:
            print(f"Seeding tasks {task_count}/{number_of_tasks}", end='\r')
            task = self.try_create_task(lane, team)
            if task is not None:
                num_assigned_users = self.faker.pyint(min_value=0, max_value=team.team_members.count())
                assigned_users = self.faker.random_elements(list(team.team_members.all()), num_assigned_users, unique=True)
                task.set_assigned_users(assigned_users)
                tasks.append(task)
                task_count += 1
        #print(f"Task seeding for {lane.lane_id} lane complete.      ")
        return tasks
        
    def set_dependencies_for_tasks(self, tasks):
        all_tasks = list(tasks)
        for task in all_tasks:
            exclude_current = all_tasks.copy()
            exclude_current.remove(task)
            
            if exclude_current:
                dependencies = self.faker.random_elements(exclude_current, length=self.faker.pyint(min_value=0,max_value=len(exclude_current)-1), unique=True)
                for x in dependencies:
                    if x not in task.dependencies.all():
                        task.dependencies.add(x)

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'


