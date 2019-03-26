from django.urls import path, include

from articles.views import home, landing_view
# from core.forms import UserLoginForm
import search.views as search_views


urlpatterns = [
    path('search', search_views.ArticlesSearchView.as_view(), name='search'),
    path('search-ac', search_views.ArticlesAutocomplete.as_view(), name='search-ac')
]

