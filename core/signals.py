from django.db.models.signals import post_save
from django.dispatch import receiver

from articles.models import Article


@receiver(post_save, sender=Article)
def index_article(sender, instance, **kwargs):
    instance.indexing()
