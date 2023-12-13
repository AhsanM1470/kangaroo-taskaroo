# Generated by Django 4.2.6 on 2023-12-13 16:31

import datetime
from django.conf import settings
import django.contrib.auth.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.query
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(max_length=30, unique=True, validators=[django.core.validators.RegexValidator(message='Username must consist of @ followed by at least three alphanumericals', regex='^@\\w{3,}$')])),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Lane',
            fields=[
                ('lane_name', models.CharField(max_length=50, validators=[django.core.validators.RegexValidator(code='invalid_lane_name', message='Enter a valid word with at least 1 alphanumeric character (no special characters allowed).', regex='^[a-zA-Z0-9 ]{1,}$')])),
                ('lane_id', models.AutoField(primary_key=True, serialize=False)),
                ('lane_order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['lane_order'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team_name', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(200)])),
                ('team_creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_teams', to=settings.AUTH_USER_MODEL)),
                ('team_members', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10)),
                ('name', models.CharField(max_length=30, validators=[django.core.validators.RegexValidator(code='invalid_word', message='Enter a valid word with at least 3 alphanumeric characters (no special characters allowed).', regex='^[a-zA-Z0-9 ]{3,}$')])),
                ('description', models.CharField(blank=True, max_length=530)),
                ('due_date', models.DateTimeField(default=datetime.datetime(1, 1, 1, 0, 0))),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('deadline_notif_sent', models.DateField(default=datetime.date(2023, 12, 12))),
                ('assigned_team', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tasks.team')),
                ('assigned_users', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
                ('lane', models.ForeignKey(default=django.db.models.query.QuerySet.first, on_delete=django.db.models.deletion.CASCADE, to='tasks.lane')),
            ],
        ),
        migrations.AddField(
            model_name='lane',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lanes', to='tasks.team'),
        ),
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invite_message', models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(100)])),
                ('status', models.CharField(default='Reject', max_length=30)),
                ('invited_users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('inviting_team', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='tasks.team')),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='notifications',
            field=models.ManyToManyField(to='tasks.notification'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        migrations.CreateModel(
            name='TaskNotification',
            fields=[
                ('notification_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tasks.notification')),
                ('notification_type', models.CharField(choices=[('AS', 'Assignment'), ('DL', 'Deadline')], default='AS', max_length=2)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.task')),
            ],
            bases=('tasks.notification',),
        ),
        migrations.AlterUniqueTogether(
            name='lane',
            unique_together={('lane_order', 'team')},
        ),
        migrations.CreateModel(
            name='InviteNotification',
            fields=[
                ('notification_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tasks.notification')),
                ('invite', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.invite')),
            ],
            bases=('tasks.notification',),
        ),
    ]
