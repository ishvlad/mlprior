import datetime

from django.contrib.auth.models import AnonymousUser
from django.db.models import Case, IntegerField, Count, When
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from articles.models import Article, BlogPost, BlogPostUser, ArticleUser, GitHubRepository, GithubRepoUser, Author, \
    NGramsMonth
from articles.serializers import ArticleDetailedSerializer, BlogPostSerializer, BlogPostUserSerializer, ArticleUserSerializer, \
    GitHubSerializer, ArticlesShortSerializer
from utils.constants import GLOBAL__COLORS, VISUALIZATION__INITIAL_NUM_BARS, GLOBAL__CATEGORIES


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


from services.github.repository import GitHubRepo


class StatsAPI(APIView):
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly
    ]

    def get(self, request):

        n_articles = Article.objects.count()

        if request.user.is_authenticated:
            articles_lib = Article.objects.filter(article_user__user=request.user, article_user__in_lib=True)
            n_articles_in_lib = articles_lib.count()
        else:
            n_articles_in_lib = 0

        n_blog_posts = BlogPost.objects.count()
        n_github_repos = GitHubRepository.objects.count()

        data = {
            'n_articles': n_articles,
            'n_articles_in_lib': n_articles_in_lib,
            'n_blog_posts': n_blog_posts,
            'n_githubs': n_github_repos,
        }

        return Response(data)


class ArticleList(viewsets.GenericViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticlesShortSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly
    ]

    def list(self, request):

        if 'library' in request.path:
            queryset = Article.objects.filter(article_user__user=self.request.user, article_user__in_lib=True)
        elif 'recommended' in request.path:
            queryset = Article.objects.all()
        elif 'recent' in request.path:
            queryset = Article.objects.order_by('-date')
        elif 'popular' in request.path:
            queryset = Article.objects.annotate(n_likes=Count(Case(
                            When(article_user__like_dislike=True, then=1),
                            output_field=IntegerField(),
                        ))).order_by('-n_likes')
            print(queryset)
        else:
            raise Exception('Unknown API link')

        page = self.request.query_params.get('page')
        if page is not None:
            paginate_queryset = self.paginate_queryset(queryset)
            serializer = self.serializer_class(paginate_queryset, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ArticlesShortSerializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, pk=None):
        article_user, is_created = ArticleUser.objects.get_or_create(user=request.user, article_id=pk)
        if 'in_lib' in request.data.keys():
            article_user.in_lib = request.data['in_lib']
        if 'like_dislike' in request.data.keys():
            article_user.like_dislike = request.data['like_dislike']
        article_user.save()

        return Response()

    def retrieve(self, request, pk=None):
        article = Article.objects.get(id=pk)

        print(request.user)

        if request.user.is_authenticated:
            article_user, is_created = ArticleUser.objects.get_or_create(user=request.user, article_id=pk)
            article_user.save()

            in_lib = article_user.in_lib
            like_dislike = article_user.like_dislike
            note = article_user.note

        else:
            in_lib = False
            like_dislike = None
            note = ''

        blogpost = BlogPost.objects.filter(article_id=pk)
        github_repo = GitHubRepository.objects.filter(article_id=pk)
        authors = Author.objects.filter(articles__id=pk)

        serializer = ArticleDetailedSerializer({
            'id': article.id,
            'title': article.title,
            'abstract': article.abstract,
            'url': article.url,
            'blog_posts': blogpost,
            'githubs': github_repo,
            'date': article.date,
            'category': article.category,
            'arxiv_id': article.arxiv_id,
            'note': note,
            'in_lib': in_lib,
            'like_dislike': like_dislike,
            'authors': authors
        }, context={'request': request})
        return Response(serializer.data)


class BlogPostAPI(viewsets.GenericViewSet):
    # pagination_class = StandardResultsSetPagination
    serializer_class = BlogPostSerializer
    queryset = BlogPost.objects.all()

    permission_classes = [
        permissions.AllowAny
    ]

    def list(self, request):
        blogpost_user = BlogPost.objects.filter(blogpostuser__user_id=request.user.id, blogpostuser__is_like=True)
        queryset = blogpost_user

        # queryset = self.paginate_queryset(queryset, request)

        page = self.request.query_params.get('page')
        if page is not None:
            paginate_queryset = self.paginate_queryset(queryset)
            serializer = self.serializer_class(paginate_queryset, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BlogPostSerializer(queryset, many=True)
        return Response(serializer.data)

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
        print('create', request.user, request.data)
        is_exists = BlogPost.objects.filter(url=request.data['url'], article_id=request.data['article_id']).count() > 0
        print(is_exists)

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
            try:
                article_id = Article.objects.get(arxiv_id=request.data['arxiv_id']).id
            except Exception as e:
                return Response({
                    'created': False
                })
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


class TrendAPI(APIView):
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly
    ]

    @staticmethod
    def date_name(resolusion, month, year):
        month -= 1

        if resolusion == 1:
            part = year + month / 12
            return datetime.date(year, month+1, 1).strftime('%b %y'), part
        if resolusion == 3:
            part = year + int(month/3) / 4
            return 'Q' + str(int(month/3)+1) + ' ' + str(year), part
        if resolusion == 6:
            part = year + int(month / 6) / 2
            return 'H' + str(int(month/6)+1) + ' ' + str(year), part
        if resolusion == 12:
            return str(year), year

    def get(self, request):
        # read params
        keywords_raw = request.query_params.get('keywords', None)
        resolution = request.query_params.get('res', 12)

        if keywords_raw is None:
            keywords_raw = 'Machine Learning, Neural Networks, Computer Vision, Deep Learning'

        # check params
        try:
            keywords_names = [kw.strip() for kw in keywords_raw.split(',')]
            keywords = [kw.lower() for kw in keywords_names]
            resolution = int(resolution)
        except Exception:
            return Response(status=400)

        if resolution != 1 and resolution != 3 and resolution != 6 and resolution != 12:
            return Response(status=400)

        # get ordered list of db rows with selected keywords
        db = NGramsMonth.objects.filter(type=1, sentences__has_any_keys=keywords).order_by('label_code')

        now = datetime.datetime.now()
        year, month = 2000, 1

        count, result = 0, []
        buf_count, buf = 0, [0] * len(keywords)
        # for each month from Jan 2000
        while not ((year == now.year and month > now.month) or year > now.year):
            # if month in DB is exactly what we want
            if db.count() != count and db[count].label_code == year * 100 + month:
                store = db[count].sentences
                for i, kw in enumerate(keywords):
                    if kw in store:
                        buf[i] += int(store[kw])

                count += 1

            buf_count += 1
            if buf_count == resolution:
                date, date_code = TrendAPI.date_name(resolution, month, year)
                item = {
                    'date': date,
                    'date_code': date_code
                }
                for i, kw in enumerate(keywords):
                    item[kw] = buf[i]

                buf_count, buf = 0, [0] * len(keywords)
                result.append(item)

            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

        if buf_count != 0:
            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1

            date, date_code = TrendAPI.date_name(resolution, month, year)
            item = {
                'date': date,
                'date_code': date_code
            }
            for i, kw in enumerate(keywords):
                item[kw] = buf[i]

            result.append(item)

        resolution_name = {
            1: 'Month',
            3: 'Quater',
            6: 'Half',
            12: 'Year'
        }

        series_options = [
            {'valueField': k, 'name': k_n} for k, k_n in zip(keywords, keywords_names)
        ]

        return Response({
            'seriesOptions': series_options,
            'resolution': resolution,
            'resolution_name': resolution_name[resolution],
            'data':  result
        })
