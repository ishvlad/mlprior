# Generated by Django 2.1.7 on 2019-06-05 16:12

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.IntegerField(default=0)),
                ('name', models.CharField(max_length=1000)),
                ('email', models.CharField(max_length=1000)),
                ('message', models.CharField(max_length=10000)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
