# Generated by Django 5.1.7 on 2025-05-22 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usercontrol_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='tg_id',
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
    ]
