# Generated by Django 2.1.7 on 2019-08-20 11:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_premium'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Premium',
            new_name='PremiumSubscription',
        ),
    ]
