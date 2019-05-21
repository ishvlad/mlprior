from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions
from rest_framework import permissions

from articles.models import Article, BlogPost, BlogPostUser, ArticleUser, GitHubRepository, GithubRepoUser
from articles.serializers import ArticleSerializer, BlogPostSerializer, BlogPostUserSerializer, ArticleUserSerializer, \
    GitHubSerializer
from rest_framework.response import Response

from services.github.repository import GitHubRepo


class ArticleList(viewsets.ViewSet):
    # queryset = Article.objects.all()
    # serializer_class = ArticleSerializer
    permission_classes = [
        permissions.AllowAny
    ]

    # def list(self, request):
    #     queryset = Article.objects.all()
    #     serializer = ArticleSerializer(queryset, many=True)
    #     return Response(serializer.data)

    def retrieve(self, request, pk=None):
        article = Article.objects.get(id=pk)

        article_user, is_created = ArticleUser.objects.get_or_create(user=request.user, article_id=pk)
        article_user.save()
        blogpost = BlogPost.objects.filter(article_id=pk)
        github_repo = GitHubRepository.objects.filter(article_id=pk)

        serializer = ArticleSerializer({
            'id': article.id,
            'title': article.title,
            'abstract': article.abstract,
            'url': article.url,
            'blog_posts': blogpost,
            'githubs': github_repo,
            'date': article.date,
            'category': article.category,
            'arxiv_id': article.arxiv_id,
            'note': article_user.note,
            'in_lib': article_user.in_lib,
            'like_dislike': article_user.like_dislike

        })
        return Response(serializer.data)


class BlogPostAPI(viewsets.ViewSet):

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

        blogpost = BlogPost.objects.create(
            title=request.data['title'],
            url=request.data['url'],
            article_id=request.data['article_id'],
            who_added=request.user
        )

        blogpost.save()

        return Response({
            'created': True
        })

    def list(self, request):
        blogpost_user = BlogPost.objects.filter(blogpostuser__user_id=request.user.id, blogpostuser__is_like=True)
        queryset = blogpost_user
        serializer = BlogPostSerializer(queryset, many=True)
        return Response(serializer.data)


class GitHubAPI(viewsets.ViewSet):
    permission_classes = [
        permissions.AllowAny
    ]

    def retrieve(self, request, pk):
        repo = GitHubRepository.objects.get(id=pk)
        serializer = GitHubSerializer(repo, many=False)
        return Response(serializer.data)

    def update(self, request, pk=None):
        print(request.user.id, pk, request.data)

        github = GitHubRepository.objects.get(id=pk)
        githubuser, is_created = GithubRepoUser.objects.get_or_create(user=request.user, github_repo=github)

        if is_created:
            githubuser.is_like = True
            github.rating += 1
        else:
            if githubuser.is_like:
                githubuser.is_like = False
                github.rating -= 1
            else:
                githubuser.is_like = True
                github.rating += 1

        githubuser.save()
        github.save()

        return Response()

    def create(self, request):
        print('API call')
        url = request.data['url']
        if 'arxiv_id' in request.data.keys():
            article_id = Article.objects.get(arxiv_id=request.data['arxiv_id']).id
        else:
            article_id = request.data['article_id']

        is_exists = GitHubRepository.objects.filter(url=url, article_id=article_id).count() > 0

        if is_exists:
            return Response({
                'created': False
            })

        g = GitHubRepo(url)

        new_git = dict(
            title=g.name,
            url=request.data['url'],
            n_stars=g.n_stars,
            language=g.language,
            languages=g.languages,
            framework=g.framework,
            article_id=article_id
        )

        if type(request.user) != AnonymousUser:
            new_git.update({
                'who_added': request.user
            })


        repo = GitHubRepository.objects.create(
            **new_git
        )

        repo.save()

        return Response({
            'created': True
        })


class BlogPostUserList(viewsets.ViewSet):
    permission_classes = [
        permissions.AllowAny
    ]

    def list(self, request):
        queryset = BlogPostUser.objects.filter(user=request.user, is_like=True)
        queryset = queryset.values_list('blog_post', flat=True)
        return Response(queryset)


class GitHubUserList(viewsets.ViewSet):
    permission_classes = [
        permissions.AllowAny
    ]

    def list(self, request):
        queryset = GithubRepoUser.objects.filter(user=request.user, is_like=True)
        queryset = queryset.values_list('github_repo', flat=True)
        return Response(queryset)


class ArticleUserList(generics.RetrieveAPIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def get_queryset(self):
        queryset = ArticleUser.objects.get(user=self.request.user, article_id=self.kwargs['pk'])

        serializer = ArticleUserSerializer(queryset, many=False)
        return Response(serializer.data)



