from rest_framework import serializers

from core.serializers import UserSerializer
from .models import Article, ArticleUser, Author, ArticleSentence, Resource, GitHub, BlogPost, ResourceUser, YouTube, \
    Reddit, WebSite, Slides
from .services import is_article_in_lib, like_dislike, get_note, is_resource_like
import numpy as np


# class BlogPostInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BlogPostInfo
#         fields = [
#             'title', 'description', 'image'
#         ]
#
#
# class BlogPostSerializer(serializers.ModelSerializer):
#     users = UserSerializer(many=True, read_only=True)
#     who_added = UserSerializer(many=False, read_only=True)
#     is_like = serializers.SerializerMethodField()
#     info = BlogPostInfoSerializer(many=False)
#     type = serializers.SerializerMethodField()
#
#     class Meta:
#         model = BlogPost
#         fields = [
#             'id', 'url', 'users', 'rating',
#             'approved', 'who_added', 'is_like',
#             'info', 'type'
#         ]
#
#     def get_is_like(self, obj):
#         user = self.context.get('request').user
#         return is_blogpost_like(obj.id, user)
#
#     def get_type(self, obj):
#         return 'resource'
#
#
# class GitHubInfoSerializer(serializers.ModelSerializer):
#     topics = serializers.SerializerMethodField()
#     languages = serializers.HStoreField()
#
#     class Meta:
#         model = GitHubInfo
#         fields = [
#             'title', 'framework', 'languages',
#             'n_stars', 'language', 'topics', 'description'
#         ]
#
#     def get_topics(self, obj):
#         return obj.topics.names()
#
#
# class GitHubSerializer(serializers.ModelSerializer):
#     users = UserSerializer(many=True, read_only=True)
#     who_added = UserSerializer(many=False, read_only=True)
#     is_like = serializers.SerializerMethodField()
#     info = GitHubInfoSerializer(many=False)
#     type = serializers.SerializerMethodField()
#
#     class Meta:
#         model = GitHubRepository
#         fields = [
#             'id', 'url', 'users', 'info',
#             'rating', 'who_added', 'is_like', 'type'
#         ]
#
#     def get_is_like(self, obj):
#         user = self.context.get('request').user
#         return is_github_like(obj.id, user)
#
#     def get_type(self, obj):
#         return 'github'


class ResourceSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    who_added = UserSerializer(many=False, read_only=True)
    is_like = serializers.SerializerMethodField()

    def to_representation(self, instance):
        print('instance', instance, type(instance))
        if isinstance(instance, GitHub):
            return GitHubSerializer(instance=instance, context=self.context).data
        elif isinstance(instance, BlogPost):
            return BlogPostSerializer(instance=instance, context=self.context).data
        elif isinstance(instance, YouTube):
            return YouTubeSerializer(instance=instance, context=self.context).data
        elif isinstance(instance, WebSite):
            return WebSiteSerializer(instance=instance, context=self.context).data
        elif isinstance(instance, Slides):
            return SlidesSerializer(instance=instance, context=self.context).data
        elif isinstance(instance, Reddit):
            return RedditSerializer(instance=instance, context=self.context).data
        else:
            raise NotImplementedError('Bad resource type')

    class Meta:
        model = Resource
        fields = [
            'id', 'url', 'users',
            'rating', 'who_added', 'is_like'
        ]

    def get_is_like(self, obj):
        print('RESOURCE')
        user = self.context.get('request').user
        return is_resource_like(obj.id, user)


class ResourceSerializerMixin:
    def get_is_like(self, obj):
        user = self.context.get('request').user
        return is_resource_like(obj.id, user)


class GitHubSerializer(ResourceSerializerMixin, serializers.ModelSerializer):
    is_like = serializers.SerializerMethodField()

    class Meta:
        model = GitHub
        depth = 2  # parameter for resource select_subclasses()
        fields = [
            'id', 'url', 'users',
            'rating', 'is_like'
        ] + [
            'title', 'description', 'n_stars', 'framework', 'type'
        ]


class BlogPostSerializer(ResourceSerializerMixin, serializers.ModelSerializer):
    is_like = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        depth = 2  # parameter for resource select_subclasses()
        fields = [
            'id', 'url', 'users',
            'rating', 'is_like'
        ] + [
            'title', 'description', 'type'
        ]


class YouTubeSerializer(ResourceSerializerMixin, serializers.ModelSerializer):
    is_like = serializers.SerializerMethodField()

    class Meta:
        model = YouTube
        depth = 2  # parameter for resource select_subclasses()
        fields = [
            'id', 'url', 'users',
            'rating', 'is_like'
        ] + [
            'title', 'description', 'type'
        ]


class RedditSerializer(ResourceSerializerMixin, serializers.ModelSerializer):
    is_like = serializers.SerializerMethodField()

    class Meta:
        model = Reddit
        depth = 2  # parameter for resource select_subclasses()
        fields = [
            'id', 'url', 'users',
            'rating', 'is_like'
        ] + [
            'title', 'description', 'type'
        ]


class WebSiteSerializer(ResourceSerializerMixin, serializers.ModelSerializer):
    is_like = serializers.SerializerMethodField()

    class Meta:
        model = WebSite
        depth = 2  # parameter for resource select_subclasses()
        fields = [
            'id', 'url', 'users',
            'rating', 'is_like'
        ] + [
            'title', 'description', 'type'
        ]


class SlidesSerializer(ResourceSerializerMixin, serializers.ModelSerializer):
    is_like = serializers.SerializerMethodField()

    class Meta:
        model = Slides
        depth = 2  # parameter for resource select_subclasses()
        fields = [
            'id', 'url', 'users',
            'rating', 'is_like'
        ] + [
            'title', 'description', 'type'
        ]


class SummarySentenceSerializer(serializers.ModelSerializer):
    nLikes = serializers.SerializerMethodField()

    class Meta:
        model = ArticleSentence
        fields = ['sentence', 'id', 'nLikes']

    def get_nLikes(self, object):
        return np.abs(5 * np.random.standard_cauchy(size=1)).astype(int)[0]


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
    summary_sentences = SummarySentenceSerializer(many=True)

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
            'has_neighbors',
            'summary_sentences'
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
    resources = ResourceSerializer(many=True, read_only=True)
    note = serializers.CharField()
    in_lib = serializers.BooleanField()
    like_dislike = serializers.NullBooleanField()
    authors = AuthorSerializer(many=True, read_only=True)
    summary_sentences = SummarySentenceSerializer(many=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'abstract', 'url', 'authors',
            'resources', 'date', 'category', 'arxiv_id',
            'note', 'in_lib', 'like_dislike', 'summary_sentences', 'has_neighbors'
        ]


class ResourceUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceUser
        fields = '__all__'
