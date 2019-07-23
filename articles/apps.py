from django.apps import AppConfig
from django.db.models.signals import post_save


class ArticlesConfig(AppConfig):
    name = 'articles'
    verbose_name = 'Articles'

    # def ready(self):
        # from articles.models import GitHubRepository, BlogPost
        # from articles.signals import github_post_save, blogpost_post_save
        # post_save.connect(github_post_save, sender=GitHubRepository)
        # post_save.connect(blogpost_post_save, sender=BlogPost)
