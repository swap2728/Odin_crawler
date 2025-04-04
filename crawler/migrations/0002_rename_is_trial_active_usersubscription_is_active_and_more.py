# Generated by Django 5.1.7 on 2025-03-26 11:13

import datetime
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usersubscription',
            old_name='is_trial_active',
            new_name='is_active',
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='usersubscription',
            name='status',
            field=models.CharField(default='trial', max_length=50),
        ),
        migrations.AlterField(
            model_name='usersubscription',
            name='subscription_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='usersubscription',
            name='trial_end',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 29, 11, 13, 39, 236459, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='usersubscription',
            name='user_id',
            field=models.IntegerField(unique=True),
        ),
    ]
