from django.core.management.base import BaseCommand, CommandError
from tasks.models import User, Team, Lane, Task, Notification, Invite

class Command(BaseCommand):
    """Build automation command to unseed the database."""
    
    help = 'Seeds the database with sample data'

    def handle(self, *args, **options):
        """Unseed the database."""

        User.objects.all().delete()
        Team.objects.all().delete()
        Lane.objects.all().delete()
        Task.objects.all().delete()
        Notification.objects.all().delete()
        Invite.objects.all().delete()
        