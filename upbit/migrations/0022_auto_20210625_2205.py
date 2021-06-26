# Generated by Django 3.2 on 2021-06-25 22:05

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('upbit', '0021_auto_20210623_0647'),
    ]

    operations = [
        migrations.AddField(
            model_name='upbitconfig',
            name='unit_count',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='market',
            name='update_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 18, 22, 5, 39, 622748, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='upbitconfig',
            name='hard_drop',
            field=models.FloatField(default=20),
        ),
    ]
