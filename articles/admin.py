from django.contrib import admin

from articles.models import Article, Author, ArticleUser, ArticleSentence

admin.site.register(Article)
admin.site.register(ArticleUser)
admin.site.register(Author)
admin.site.register(ArticleSentence)
