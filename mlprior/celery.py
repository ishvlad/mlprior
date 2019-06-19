

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mlprior.settings')

app = Celery('mlprior')
app.config_from_object('django.conf:settings')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'update_githubs_each_week': {
        'task': 'mlprior.articles.tasks.trigger_github_updates',
        'schedule': crontab(day_of_week=1),
    },
    'update_resources_each_week': {
        'task': 'mlprior.articles.tasks.trigger_resources_updates',
        'schedule': crontab()
    }
}
