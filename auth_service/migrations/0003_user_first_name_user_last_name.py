# Generated by Django 5.1.5 on 2025-02-09 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_service', '0002_rename_user_id_user_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='first_name',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='last_name',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
