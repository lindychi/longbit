# Generated by Django 3.2 on 2021-06-15 08:25

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('upbit', '0011_auto_20210615_0800'),
    ]

    operations = [
        migrations.AddField(
            model_name='coinmarket',
            name='english_name',
            field=models.CharField(default='', max_length=64),
        ),
        migrations.AddField(
            model_name='coinmarket',
            name='korean_name',
            field=models.CharField(default='', max_length=64),
        ),
        migrations.AddField(
            model_name='coinmarket',
            name='market_warning',
            field=models.CharField(default='', max_length=64),
        ),
        migrations.AlterField(
            model_name='market',
            name='update_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 8, 8, 25, 36, 128620, tzinfo=utc)),
        ),
    ]
