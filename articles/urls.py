from django.urls import path, include
from articles import views

urlpatterns = [
    path('', views.articles, name='articles'),
    # path('<int:article_id>/', views.article_detail, name='article-detail'),
]
