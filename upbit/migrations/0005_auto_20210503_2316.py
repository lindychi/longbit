# Generated by Django 3.2 on 2021-05-03 23:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upbit', '0004_auto_20210503_2304'),
    ]

    operations = [
        migrations.AddField(
            model_name='market',
            name='ask_min',
            field=models.FloatField(default=5500.0),
        ),
        migrations.AddField(
            model_name='market',
            name='bid_min',
            field=models.FloatField(default=5500.0),
        ),
    ]
