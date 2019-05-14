from django.contrib import admin

from articles.models import Article, Author, BlogPost

admin.site.register(Article)
admin.site.register(BlogPost)
admin.site.register(Author)
