from django.contrib.auth.decorators import login_required
from django.urls import path

from articles import views
import core.views as core_views

urlpatterns = [
    path('recommended', login_required(views.ArticlesView.as_view(), login_url='/accounts/login'), name='articles'),
    path('recent', login_required(views.ArticlesView.as_view(), login_url='/accounts/login'), name='articles'),
    path('popular', login_required(views.ArticlesView.as_view(), login_url='/accounts/login'), name='articles'),
    path('library', login_required(views.ArticlesLibrary.as_view(), login_url='/accounts/login'), name='library'),
    path('liked', login_required(views.LikedDisliked.as_view(), login_url='/accounts/login'), name='liked'),
    path('disliked', login_required(views.LikedDisliked.as_view(), login_url='/accounts/login'), name='disliked'),

    path('details/<int:pk>', views.ArticleDetailsView.as_view(), name='article_details'),
    path('authors/<author_name>', login_required(views.ArticlesOfAuthor.as_view(), login_url='/accounts/login'), name='author_articles'),
    path('api/v1/library/add/<article_id>', login_required(views.add_remove_from_library, login_url='/accounts/login'), name='lib_add'),
    path('api/v1/library/remove/<article_id>', login_required(views.add_remove_from_library, login_url='/accounts/login'), name='lib_remove'),
    path('api/v1/note/update/<article_id>', login_required(views.change_note, login_url='/accounts/login'), name='change_note'),
    path('api/v1/like/<article_id>', login_required(views.like_dislike, login_url='/accounts/login'), name='like'),
    path('api/v1/dislike/<article_id>', login_required(views.like_dislike, login_url='/accounts/login'), name='dislike'),
    path('api/v1/trend', views.trend_view, name='trend_view'),
    # path('api/articles/search/<searchinput>', core_views.search, name='search'),


]
