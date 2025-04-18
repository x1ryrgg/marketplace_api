# Generated by Django 5.1.7 on 2025-04-12 15:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_control_api', '0005_alter_product_description_and_more'),
        ('seller_store_api', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='product_control_api.productvariant'),
        ),
    ]
