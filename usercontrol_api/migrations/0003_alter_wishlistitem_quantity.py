# Generated by Django 5.1.7 on 2025-04-05 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usercontrol_api', '0002_alter_wishlistitem_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wishlistitem',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
