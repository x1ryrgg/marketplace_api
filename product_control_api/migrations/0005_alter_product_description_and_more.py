# Generated by Django 5.1.7 on 2025-04-12 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_control_api', '0004_alter_productvariant_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.CharField(blank=True, default='Продавец не оставил описание о товаре.', max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='productvariant',
            name='description',
            field=models.CharField(blank=True, default='Продавец не оставил описание о товаре.', max_length=500),
        ),
    ]
