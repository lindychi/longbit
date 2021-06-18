# Generated by Django 3.2 on 2021-06-15 08:42

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('upbit', '0013_auto_20210615_0837'),
    ]

    operations = [
        migrations.AddField(
            model_name='coinmarket',
            name='buy_balance',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='market',
            name='update_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 8, 8, 42, 26, 313420, tzinfo=utc)),
        ),
    ]
