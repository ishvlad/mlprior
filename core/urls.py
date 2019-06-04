from django.urls import path, include

from articles.views import home
# from core.forms import UserLoginForm

from core.views import LandingView, RegistrationAPIView, LoginAPIView, UserRetrieveUpdateAPIView

from articles.api import BlogPostAPI, ArticleList, BlogPostUserList, GitHubAPI, GitHubUserList, StatsAPI, \
    TrendAPI, CategoriesAPI
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'blogposts', BlogPostAPI, base_name='blogposts')
router.register(r'articles/recommended', ArticleList, base_name='articleslist')
router.register(r'articles/recent', ArticleList, base_name='articleslist')
router.register(r'articles/popular', ArticleList, base_name='articleslist')
router.register(r'articles/library', ArticleList, base_name='articleslist')
router.register(r'articles/details', ArticleList, base_name='articleslist')
router.register(r'blogpostuser', BlogPostUserList, base_name='blogpostuser')
router.register(r'githubuser', GitHubUserList, base_name='githubuser')
router.register(r'githubs', GitHubAPI, base_name='githubs')

apiurls = [
    path('api/', include(router.urls)),
    path('api/stats', StatsAPI.as_view()),

    path('api/visualization/trends', TrendAPI.as_view()),
    path('api/visualization/categories', CategoriesAPI.as_view())
]


urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('home/', home, name='home'),
    # path('feedback/', FeedbackView.as_view(), name='feedback'),
    path('user', UserRetrieveUpdateAPIView.as_view()),
    path('users/', RegistrationAPIView.as_view()),
    path('users/login', LoginAPIView.as_view()),
    # path('accounts/', include('allauth.urls')),
    # path('auth/', include('social_django.urls', namespace='social'))
] + apiurls
