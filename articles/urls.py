from django.contrib.auth.decorators import login_required
from django.urls import path

from articles import views

# blogpost_router = routers.DefaultRouter()
# blogpost_router.register(r'blogposts', BlogPostAPI, base_name='blogposts')
# blogpost_router.register(r'articles/recommended', ArticleList, base_name='articleslist')
# blogpost_router.register(r'articles/recent', ArticleList, base_name='articleslist')
# blogpost_router.register(r'articles/popular', ArticleList, base_name='articleslist')
# blogpost_router.register(r'articles/library', ArticleList, base_name='articleslist')
# blogpost_router.register(r'blogpostuser', BlogPostUserList, base_name='blogpostuser')
# blogpost_router.register(r'githubuser', GitHubUserList, base_name='githubuser')
# blogpost_router.register(r'githubs', GitHubAPI, base_name='githubs')
#
# apiurls = [
#     path('api/', include(blogpost_router.urls)),
#
# ]

urlpatterns = []
