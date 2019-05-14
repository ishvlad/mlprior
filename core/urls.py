from django.urls import path, include

from articles.views import home
# from core.forms import UserLoginForm
from core.views import FeedbackView, LandingView


urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('home/', home, name='home'),
    path('feedback/', FeedbackView.as_view(), name='feedback'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('social_django.urls', namespace='social'))
]
