# Generated by Django 2.1.7 on 2019-07-07 11:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0008_auto_20190707_0343'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='articlesentence',
            name='importance',
        ),
    ]
