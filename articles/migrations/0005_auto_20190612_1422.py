# Generated by Django 2.1.7 on 2019-06-12 14:22

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('articles', '0004_auto_20190605_1617'),
    ]

    operations = [
        migrations.AddField(
            model_name='githubrepository',
            name='description',
            field=models.TextField(default='', verbose_name='description'),
        ),
        migrations.AddField(
            model_name='githubrepository',
            name='is_official',
            field=models.BooleanField(default=False, verbose_name='is_official'),
        ),
        migrations.AddField(
            model_name='githubrepository',
            name='topics',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
