# Generated by Django 5.1.7 on 2025-04-10 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seller_store_api', '0008_alter_review_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='comments/'),
        ),
    ]
