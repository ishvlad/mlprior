from rest_framework import serializers

from core.serializers import UserSerializer
from .models import BlogPost, Article, BlogPostUser, ArticleUser, GitHubRepository, GithubRepoUser
from rest_framework.fields import CurrentUserDefault


class BlogPostSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    who_added = UserSerializer(many=False, read_only=True)

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'url', 'users', 'rating', 'approved', 'who_added']


class GitHubSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    who_added = UserSerializer(many=False, read_only=True)

    class Meta:
        model = GitHubRepository
        fields = ['id', 'title', 'url', 'users', 'rating', 'who_added', 'n_stars', 'language']


class ArticleUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArticleUser
        fields = ['note', 'like_dislike', 'in_lib']


class ArticleSerializer(serializers.ModelSerializer):
    blog_posts = BlogPostSerializer(many=True, read_only=True)
    githubs = GitHubSerializer(many=True, read_only=True)
    note = serializers.CharField()
    in_lib = serializers.BooleanField()
    like_dislike = serializers.NullBooleanField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'abstract', 'url',
            'blog_posts', 'githubs',
            'date', 'category', 'arxiv_id',
            'note', 'in_lib', 'like_dislike'
        ]


class BlogPostUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPostUser
        fields = '__all__'


class GitHubUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GithubRepoUser
        fields = '__all__'







