# Generated by Django 3.2 on 2021-06-18 07:35

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('upbit', '0015_auto_20210618_0725'),
    ]

    operations = [
        migrations.AddField(
            model_name='coinmarket',
            name='ticker_update',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 18, 7, 35, 0, 604091, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='market',
            name='update_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 11, 7, 35, 0, 603556, tzinfo=utc)),
        ),
    ]
