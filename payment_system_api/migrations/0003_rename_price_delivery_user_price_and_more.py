# Generated by Django 5.1.7 on 2025-04-10 08:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment_system_api', '0002_history_status_alter_history_created_at_delivery'),
        ('seller_store_api', '0003_delete_history'),
    ]

    operations = [
        migrations.RenameField(
            model_name='delivery',
            old_name='price',
            new_name='user_price',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='price',
            new_name='user_price',
        ),
        migrations.RemoveField(
            model_name='delivery',
            name='name',
        ),
        migrations.RemoveField(
            model_name='history',
            name='name',
        ),
        migrations.AddField(
            model_name='delivery',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='seller_store_api.product'),
        ),
        migrations.AddField(
            model_name='history',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='seller_store_api.product'),
        ),
    ]
