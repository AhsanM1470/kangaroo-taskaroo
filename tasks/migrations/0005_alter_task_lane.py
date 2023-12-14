# Generated by Django 4.2.6 on 2023-12-13 16:57

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.query


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_alter_task_deadline_notif_sent_alter_task_lane'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='lane',
            field=models.ForeignKey(default=django.db.models.query.QuerySet.first, on_delete=django.db.models.deletion.CASCADE, to='tasks.lane'),
        ),
    ]
