# Generated by Django 5.1.5 on 2025-02-09 09:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth_service', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='user_id',
            new_name='id',
        ),
    ]
