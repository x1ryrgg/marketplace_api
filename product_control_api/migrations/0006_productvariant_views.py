# Generated by Django 5.1.7 on 2025-04-15 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_control_api', '0005_alter_product_description_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='views',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
