# Generated by Django 4.2.6 on 2023-11-29 16:19

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_invite_inviting_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='team_creator',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='created_teams', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='invite',
            name='invite_message',
            field=models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(100)]),
        ),
        migrations.AlterField(
            model_name='team',
            name='description',
            field=models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(200)]),
        ),
    ]