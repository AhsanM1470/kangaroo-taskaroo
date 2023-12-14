# Generated by Django 4.2.6 on 2023-12-14 12:29

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.query
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_alter_task_deadline_notif_sent_alter_task_due_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateTimeField(default=django.utils.timezone.now, validators=[django.core.validators.MinValueValidator(limit_value=datetime.datetime(2023, 12, 14, 12, 29, 1, 254113, tzinfo=datetime.timezone.utc), message='Datetime must be in the future.')]),
        ),
        migrations.AlterField(
            model_name='task',
            name='lane',
            field=models.ForeignKey(default=django.db.models.query.QuerySet.first, on_delete=django.db.models.deletion.CASCADE, to='tasks.lane'),
        ),
    ]
