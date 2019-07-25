from django.contrib import admin

from articles.models import Article, Author, ArticleUser, ArticleSentence, BlogPost, GitHub, YouTube, Reddit, WebSite, Slides

admin.site.register(Article)
admin.site.register(ArticleUser)
admin.site.register(Author)
admin.site.register(ArticleSentence)
admin.site.register(BlogPost)
admin.site.register(GitHub)
admin.site.register(YouTube)
admin.site.register(Reddit)
admin.site.register(WebSite)
admin.site.register(Slides)
