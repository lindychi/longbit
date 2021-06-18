# Generated by Django 3.2 on 2021-06-15 08:00

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('upbit', '0010_alter_market_update_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='market',
            name='update_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 8, 8, 0, 34, 206241, tzinfo=utc)),
        ),
        migrations.CreateModel(
            name='CoinMarket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('market', models.CharField(max_length=64)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
