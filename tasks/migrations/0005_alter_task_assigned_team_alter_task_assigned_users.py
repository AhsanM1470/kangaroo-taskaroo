# Generated by Django 4.2.6 on 2023-12-05 15:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_remove_user_tasks_task_assigned_team_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='assigned_team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.team'),
        ),
        migrations.AlterField(
            model_name='task',
            name='assigned_users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
