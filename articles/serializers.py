from rest_framework import serializers

from core.serializers import UserSerializer
from .models import BlogPost, Article, BlogPostUser, ArticleUser, GitHubRepository, GithubRepoUser, Author
from rest_framework.fields import CurrentUserDefault, HStoreField
from rest_framework.pagination import PageNumberPagination
from .services import is_article_in_lib, like_dislike, get_note, is_blogpost_like, is_github_like


class BlogPostSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    who_added = UserSerializer(many=False, read_only=True)
    is_like = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'url', 'users', 'rating', 'approved', 'who_added', 'is_like']

    def get_is_like(self, obj):
        user = self.context.get('request').user
        return is_blogpost_like(obj.id, user)


class GitHubSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    who_added = UserSerializer(many=False, read_only=True)
    languages = serializers.HStoreField()
    is_like = serializers.SerializerMethodField()

    class Meta:
        model = GitHubRepository
        fields = ['id', 'title', 'url', 'users',
                  'rating', 'framework', 'languages',
                  'who_added', 'n_stars', 'language', 'is_like']

    def get_is_like(self, obj):
        user = self.context.get('request').user
        return is_github_like(obj.id, user)


class ArticleUserSerializer(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = ArticleUser
        fields = ['note', 'like_dislike', 'in_lib']


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['name']


class ArticlesShortSerializer(serializers.ModelSerializer):
    # title = serializers.CharField()
    # abstract = serializers.CharField()
    in_lib = serializers.SerializerMethodField()
    like_dislike = serializers.SerializerMethodField()
    note = serializers.SerializerMethodField()
    authors = AuthorSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'abstract',
            'authors',
            'url',
            'arxiv_id',
            'date',
            'category',
            'in_lib',
            'like_dislike',
            'note',
            'has_neighbors'
        ]

    def get_in_lib(self, obj):
        user = self.context.get('request').user
        return is_article_in_lib(obj.id, user)

    def get_like_dislike(self, obj):
        user = self.context.get('request').user
        return like_dislike(obj.id, user)

    def get_note(self, obj):
        user = self.context.get('request').user
        return get_note(obj.id, user)


class ArticleDetailedSerializer(serializers.ModelSerializer):
    blog_posts = BlogPostSerializer(many=True, read_only=True)
    githubs = GitHubSerializer(many=True, read_only=True)
    note = serializers.CharField()
    in_lib = serializers.BooleanField()
    like_dislike = serializers.NullBooleanField()
    authors = AuthorSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'abstract', 'url', 'authors',
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







