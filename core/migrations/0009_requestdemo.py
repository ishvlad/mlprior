# Generated by Django 2.1.7 on 2019-09-24 12:59

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20190821_0813'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestDemo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.IntegerField(default=0)),
                ('name', models.CharField(max_length=1000)),
                ('email', models.CharField(max_length=1000)),
                ('feature', models.IntegerField(default=0)),
                ('message', models.TextField(max_length=10000)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
