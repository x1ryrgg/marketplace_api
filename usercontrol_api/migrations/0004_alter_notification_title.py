# Generated by Django 5.1.7 on 2025-06-07 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usercontrol_api', '0003_alter_user_tg_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='title',
            field=models.CharField(blank=True, choices=[('purchase', 'покупка'), ('delivery', 'доставка'), ('coupon', 'купон'), ('seller', 'продавец'), ('other', 'другое')], default='other', max_length=50),
        ),
    ]
