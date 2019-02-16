from django.urls import path

from articles import views

urlpatterns = [
    path('recommended', views.ArticlesView.as_view(), name='articles'),
    path('recent', views.ArticlesView.as_view(), name='articles'),
    path('popular', views.ArticlesView.as_view(), name='articles'),
    path('library', views.ArticlesLibrary.as_view(), name='library'),
    path('liked', views.LikedDisliked.as_view(), name='liked'),
    path('disliked', views.LikedDisliked.as_view(), name='disliked'),

    path('details/<int:pk>', views.ArticleDetailsView.as_view(), name='article_details'),
    path('authors/<author_name>', views.ArticlesOfAuthor.as_view(), name='author_articles'),
    path('api/v1/library/add/<article_id>', views.add_remove_from_library, name='lib_add'),
    path('api/v1/library/remove/<article_id>', views.add_remove_from_library, name='lib_remove'),
    path('api/v1/note/update/<article_id>', views.change_note, name='change_note'),
    path('api/v1/like/<article_id>', views.like_dislike, name='like'),
    path('api/v1/dislike/<article_id>', views.like_dislike, name='dislike'),
    path('api/v1/trend', views.trend_view, name='trend_view')
    # path('api/articles/search/<searchinput>', articles_views.search, name='search'),


]
