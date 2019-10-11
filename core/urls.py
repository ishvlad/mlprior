from django.urls import path, include
from rest_framework import routers
from rest_framework.documentation import include_docs_urls

from articles.api import ArticlesAPI, StatsAPI, \
    TrendAPI, CategoriesAPI, SummaryAPI, ResourceAPI
from core.views import RegistrationAPIView, LoginAPIView, UserRetrieveUpdateAPIView, FeedbackAPI, \
    MixPanelAPI, SubscriptionAPI, ProfileRetrieveAPIView, RequestDemoAPI, FileUploadView

# from core.forms import UserLoginForm

router = routers.DefaultRouter()
router.register(r'resources', ResourceAPI, base_name='resources')
router.register(r'articles', ArticlesAPI, base_name='articleslist')
router.register(r'articles/details', ArticlesAPI, base_name='articleslist')
router.register(r'summary/feedback', SummaryAPI, base_name='summaryfeedback')
# router.register(r'blogpostuser', BlogPostUserList, base_name='blogpostuser')
# router.register(r'githubuser', GitHubUserList, base_name='githubuser')
# router.register(r'githubs', GitHubAPI, base_name='githubs')

apiurls = [
    path('api/', include(router.urls)),
    path('api/stats', StatsAPI.as_view()),
    path('api/feedback', FeedbackAPI.as_view()),
    path('api/requestdemo', RequestDemoAPI.as_view()),
    path('api/mplog', MixPanelAPI.as_view()),
    path('api/premium', SubscriptionAPI.as_view()),
    path('api/profile', ProfileRetrieveAPIView.as_view()),
    path('api/user', UserRetrieveUpdateAPIView.as_view()),
    path('api/auth/signup', RegistrationAPIView.as_view()),
    path('api/auth/login', LoginAPIView.as_view()),
    path('api/visualization/trends', TrendAPI.as_view()),
    path('api/visualization/categories', CategoriesAPI.as_view()),
    path('api/upload', FileUploadView.as_view())
]

urlpatterns = [
  path('docs/', include_docs_urls(title='ML p(r)ior API'))
] + apiurls
