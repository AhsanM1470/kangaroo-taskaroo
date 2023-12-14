from django.core.management.base import BaseCommand
from tasks.models import Team
from tasks.models import User as CustomUser

class Command(BaseCommand):
    help = 'Create a superuser with custom fields and related object'

    def handle(self, *args, **options):
        username = input('Enter username: ')
        first_name = input('Enter first name: ')
        last_name = input('Enter last name: ')
        email = input('Enter email: ')
        password = input('Enter password: ')

        user = CustomUser.objects.create_superuser(username=username, email=email, password=password, first_name=first_name, last_name=last_name)

        team_name = input('Enter team name: ')
        team_creator = user
        team = Team.objects.create(
            team_name=team_name,
            team_creator=team_creator
            )
        team.add_invited_member(user)

        self.stdout.write(self.style.SUCCESS(f'Superuser {username} and Team {team_name} instance created successfully!'))