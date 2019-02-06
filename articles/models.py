from django.db import models
from django.contrib.auth.models import User


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

    users = models.ManyToManyField(User, 'articles')

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

#
# class Authorship(models.Model):
#     author = models.ForeignKey(Author, on_delete=models.CASCADE)
#     article = models.ForeignKey(Article, on_delete=models.CASCADE)

#
