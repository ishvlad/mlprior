from rest_framework import serializers

from core.serializers import UserSerializer
from .models import BlogPost, Article, BlogPostUser, ArticleUser
from rest_framework.fields import CurrentUserDefault


class BlogPostSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    who_added = UserSerializer(many=False, read_only=True)

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'url', 'users', 'rating', 'approved', 'who_added']


class ArticleUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArticleUser
        fields = ['note', 'like_dislike', 'in_lib']


class ArticleSerializer(serializers.ModelSerializer):
    blog_post = BlogPostSerializer(many=True, read_only=True)
    note = serializers.CharField()
    in_lib = serializers.BooleanField()
    like_dislike = serializers.NullBooleanField()


    class Meta:
        model = Article
        fields = ['id', 'title', 'abstract', 'url', 'blog_post', 'date', 'category', 'arxiv_id', 'note', 'in_lib', 'like_dislike']


class BlogPostUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPostUser
        fields = '__all__'







