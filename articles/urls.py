from django.urls import path

from articles import views

urlpatterns = [
    path('', views.articles, name='articles'),
    path('details/<article_id>', views.article_details, name='article_details'),
    path('api/v1/library/add/<article_id>', views.add_remove_from_library, name='lib_add'),
    path('api/v1/library/remove/<article_id>', views.add_remove_from_library, name='lib_remove'),

    path('api/v1/note/update/<article_id>', views.change_note, name='change_note'),
    # path('api/articles/search/<searchinput>', articles_views.search, name='search'),
    path('library', views.library, name='library'),
]
