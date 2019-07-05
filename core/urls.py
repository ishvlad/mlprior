from django.urls import path, include
from rest_framework import routers
from rest_framework.documentation import include_docs_urls

from articles.api import BlogPostAPI, ArticleList, BlogPostUserList, GitHubAPI, GitHubUserList, StatsAPI, \
    TrendAPI, CategoriesAPI
from articles.views import home
from core.views import LandingView, RegistrationAPIView, LoginAPIView, UserRetrieveUpdateAPIView, FeedbackAPI

# from core.forms import UserLoginForm

router = routers.DefaultRouter()
router.register(r'blogposts', BlogPostAPI, base_name='blogposts')
router.register(r'articles/recommended', ArticleList, base_name='articleslist')
router.register(r'articles/recent', ArticleList, base_name='articleslist')
router.register(r'articles/popular', ArticleList, base_name='articleslist')
router.register(r'articles/saved', ArticleList, base_name='articleslist')
router.register(r'articles/liked', ArticleList, base_name='articleslist')
router.register(r'articles/disliked', ArticleList, base_name='articleslist')
router.register(r'articles/details', ArticleList, base_name='articleslist')
router.register(r'articles/related', ArticleList, base_name='articleslist')
router.register(r'blogpostuser', BlogPostUserList, base_name='blogpostuser')
router.register(r'githubuser', GitHubUserList, base_name='githubuser')
router.register(r'githubs', GitHubAPI, base_name='githubs')

apiurls = [
    path('api/', include(router.urls)),
    path('api/stats', StatsAPI.as_view()),
    path('api/feedback', FeedbackAPI.as_view()),
    path('api/user', UserRetrieveUpdateAPIView.as_view()),
    path('api/auth/signup', RegistrationAPIView.as_view()),
    path('api/auth/login', LoginAPIView.as_view()),

    path('api/visualization/trends', TrendAPI.as_view()),
    path('api/visualization/categories', CategoriesAPI.as_view())
]

urlpatterns = [
  path('', LandingView.as_view(), name='landing'),
  path('home/', home, name='home'),
  path('docs/', include_docs_urls(title='ML p(r)ior API'))
] + apiurls
