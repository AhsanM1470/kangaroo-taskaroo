# Generated by Django 4.2.6 on 2023-12-11 02:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0014_lane_team'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lane',
            name='lane_order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterUniqueTogether(
            name='lane',
            unique_together={('lane_order', 'team')},
        ),
    ]
