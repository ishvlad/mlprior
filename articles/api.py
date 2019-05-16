from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions
from rest_framework import permissions

from articles.models import Article, BlogPost, BlogPostUser, ArticleUser
from articles.serializers import ArticleSerializer, BlogPostSerializer, BlogPostUserSerializer, ArticleUserSerializer
from rest_framework.response import Response


class ArticleList(viewsets.ViewSet):
    # queryset = Article.objects.all()
    # serializer_class = ArticleSerializer
    permission_classes = [
        permissions.AllowAny
    ]

    def list(self, request):
        queryset = Article.objects.all()
        serializer = ArticleSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        article = Article.objects.get(id=pk)

        article_user, is_created = ArticleUser.objects.get_or_create(user=request.user, article_id=pk)
        article_user.save()
        blogpost = BlogPost.objects.filter(article_id=pk)

        serializer = ArticleSerializer({
            'id': article.id,
            'title': article.title,
            'abstract': article.abstract,
            'url': article.url,
            'blog_post': blogpost,
            'date': article.date,
            'category': article.category,
            'arxiv_id': article.arxiv_id,
            'note': article_user.note,
            'in_lib': article_user.in_lib,
            'like_dislike': article_user.like_dislike
        })
        return Response(serializer.data)


class BlogPostList(viewsets.ViewSet):

    permission_classes = [
        permissions.AllowAny
    ]

    def update(self, request, pk=None):
        print(request.user.id, pk, request.data)

        blog_post = BlogPost.objects.get(id=pk)
        blogpostuser, is_created = BlogPostUser.objects.get_or_create(user=request.user, blog_post=blog_post)

        if is_created:
            blogpostuser.is_like = True
            blog_post.rating += 1
        else:
            if blogpostuser.is_like:
                blogpostuser.is_like = False
                blog_post.rating -= 1
            else:
                blogpostuser.is_like = True
                blog_post.rating += 1

        blogpostuser.save()
        blog_post.save()

        return Response()

    def create(self, request):
        is_exists = BlogPost.objects.filter(url=request.data['url'], article_id=request.data['article_id']).count() > 0

        if is_exists:
            return Response({
                'created': False
            })

        blogpost = BlogPost.objects.create(title=request.data['title'],
                                           url=request.data['url'],
                                           article_id=request.data['article_id'],
                                           who_added=request.user)

        blogpost.save()

        return Response({
            'created': True
        })

    def list(self, request):
        blogpost_user = BlogPost.objects.filter(blogpostuser__user_id=request.user.id, blogpostuser__is_like=True)
        queryset = blogpost_user
        serializer = BlogPostSerializer(queryset, many=True)
        return Response(serializer.data)


class BlogPostUserList(viewsets.ViewSet):
    permission_classes = [
        permissions.AllowAny
    ]

    def list(self, request):
        queryset = BlogPostUser.objects.filter(user=request.user, is_like=True)
        queryset = queryset.values_list('blog_post', flat=True)
        return Response(queryset)


class ArticleUserList(generics.RetrieveAPIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def get_queryset(self):
        queryset = ArticleUser.objects.get(user=self.request.user, article_id=self.kwargs['pk'])

        serializer = ArticleUserSerializer(queryset, many=False)
        return Response(serializer.data)



