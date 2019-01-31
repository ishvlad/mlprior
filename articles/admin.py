from django.contrib import admin

from articles.models import Article, Author


admin.site.register(Article)
admin.site.register(Author)
