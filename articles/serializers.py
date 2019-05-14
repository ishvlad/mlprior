from rest_framework import serializers

from core.serializers import UserSerializer
from .models import BlogPost, Article, BlogPostUser


class BlogPostSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'url', 'users', 'rating']


class ArticleSerializer(serializers.ModelSerializer):
    blog_post = BlogPostSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = ['title', 'url', 'blog_post']


class BlogPostUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPostUser
        fields = '__all__'







