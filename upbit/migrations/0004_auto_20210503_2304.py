# Generated by Django 3.2 on 2021-05-03 23:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('upbit', '0003_market_market'),
    ]

    operations = [
        migrations.AddField(
            model_name='market',
            name='currency',
            field=models.CharField(default='', max_length=32),
        ),
        migrations.AddField(
            model_name='market',
            name='unit_currency',
            field=models.CharField(default='KRW', max_length=64),
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField()),
                ('side', models.CharField(max_length=12)),
                ('price', models.FloatField()),
                ('volume', models.FloatField()),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('market', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='upbit.market')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
