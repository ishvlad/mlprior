from django.apps import AppConfig
from django.db.models.signals import post_save


class ArticlesConfig(AppConfig):
    name = 'articles'
    verbose_name = 'Articles'

    def ready(self):
        from articles.models import GitHub, BlogPost, YouTube, Slides, Reddit, WebSite
        from articles.signals import github_post_save, blogpost_post_save, reddit_post_save, website_post_save, slides_post_save, youtube_post_save
        post_save.connect(github_post_save, sender=GitHub)
        post_save.connect(blogpost_post_save, sender=BlogPost)
        post_save.connect(youtube_post_save, sender=YouTube)
        post_save.connect(slides_post_save, sender=Slides)
        post_save.connect(reddit_post_save, sender=Reddit)
        post_save.connect(website_post_save, sender=WebSite)
