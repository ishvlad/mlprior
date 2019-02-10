from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Article(models.Model):
    arxiv_id = models.CharField(max_length=50)
    version = models.CharField(max_length=10, verbose_name='Version')

    title = models.CharField(max_length=1000, verbose_name='Title')
    abstract = models.TextField(verbose_name='Abstract')
    url = models.URLField(verbose_name='URL')
    date = models.DateField()
    category = models.CharField(max_length=100)

    note = models.TextField(verbose_name='Note', default='')

    users = models.ManyToManyField(User, 'articles', through='ArticleUser')
    related = models.ManyToManyField('self', 'related_articles', through='ArticleArticleRelation',
          symmetrical=False)

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['date']

    def __str__(self):
        return self.title


class Author(models.Model):
    name = models.CharField(max_length=100, verbose_name='Author name', primary_key=True)

    articles = models.ManyToManyField(Article, 'authors')

    class Meta:
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'
        ordering = ['name']

    def __str__(self):
        return self.name


class ArticleUser(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    like_dislike = models.NullBooleanField()
    in_lib = models.BooleanField(default=False)


class ArticleArticleRelation(models.Model):
    left = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='from_article')
    right = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='to_article')

    distance = models.FloatField()

#
# class Authorship(models.Model):
#     author = models.ForeignKey(Author, on_delete=models.CASCADE)
#     article = models.ForeignKey(Article, on_delete=models.CASCADE)

#
