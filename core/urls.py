from django.urls import path, include

from articles.views import home, landing_view
# from core.forms import UserLoginForm
from core.views import FeedbackView


urlpatterns = [
    path('', landing_view, name='landing'),
    path('home/', home, name='home'),
    path('feedback/', FeedbackView.as_view(), name='feedback'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('social_django.urls', namespace='social'))
]
