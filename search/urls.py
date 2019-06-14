from django.urls import path, include
from rest_framework import routers

import search.views as search_views
from search.api import SearchAPI

urlpatterns = [
    # path('search', search_views.ArticlesSearchView.as_view(), name='search'),
    # path('search-ac', search_views.ArticlesAutocomplete.as_view(), name='search-ac')
]

router = routers.DefaultRouter()
router.register(r'articles/search', SearchAPI, base_name='search')

apiurls = [
    path('api/', include(router.urls)),

]

urlpatterns += apiurls