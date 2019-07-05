import json

from django.contrib.auth.models import AnonymousUser
from django.db.models import Case, IntegerField, Count, When, Q
from django.shortcuts import get_object_or_404
from github import UnknownObjectException
from rest_framework import permissions
from rest_framework import viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from articles.models import Article, BlogPost, BlogPostUser, ArticleUser, GitHubRepository, GithubRepoUser, Author, \
    NGramsMonth, Categories, DefaultStore, UserTags
from articles.serializers import ArticleDetailedSerializer, BlogPostSerializer, ArticleUserSerializer, \
    GitHubSerializer, ArticlesShortSerializer
from core.models import Feedback
from services.github.repository import GitHubRepo
from utils.recommendation import RelationModel
from utils.http import _success, _error


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


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


def get_related_articles(article: Article):
    if not article.has_neighbors:
        return Article.objects.none()

    # sort nn by distance
    neighbors = article.articletext.relations
    neighbors_sorted = sorted(neighbors.items(), key=lambda x: float(x[1]))

    # get sorted ids, create order for Django and order resulting articles
    ids = [int(x[0]) for x in neighbors_sorted]
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
    queryset = Article.objects.filter(pk__in=ids).order_by(preserved)
    return queryset


def get_recommended_articles(request):
    articles_positive = ArticleUser.objects.filter(
        Q(like_dislike=True) | Q(in_lib=True),
        user=request.user, article__has_neighbors=True
    )

    # no saved or liked articles
    if articles_positive.count() == 0:
        return Article.objects.none()

    # get IDs from seen articles
    viewed_articles_id = list(ArticleUser.objects.filter(
        Q(like_dislike=True) | Q(like_dislike=False) | Q(in_lib=True),
        user=request.user
    ).values_list('id', flat=True))

    # get relations from 50 last liked articles
    relations = articles_positive.order_by('-id')[:50].values('article__articletext__relations')

    # get nearest articles from each relation
    result = {}
    for relation in relations:
        relation = relation['article__articletext__relations']
        relation = sorted(relation.items(), key=lambda x: x[1])

        # collect in 'result' all relations with min distance
        for k, v in relation:
            if int(k) not in viewed_articles_id:
                if k not in result or v < result[k]:
                    result[k] = v

    # (very rare case) -- user disliked all articles in DB except of one (which is saved or liked)
    if len(result) == 0:
        return Article.objects.none()

    # get nearest 'n_result' articles from 'result'
    n_result = 1000
    result = sorted(result.items(), key=lambda x: x[1])[:n_result]

    # get sorted ids, create order for Django and order resulting articles
    ids = [int(x[0]) for x in result]
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
    queryset = Article.objects.filter(pk__in=ids).order_by(preserved)
    return queryset


class ArticleList(viewsets.GenericViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticlesShortSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly
    ]

    def get_queryset(self):
        if 'saved' in self.request.path:
            queryset = Article.objects.filter(article_user__user=self.request.user, article_user__in_lib=True)
        elif 'disliked' in self.request.path:
            queryset = Article.objects.filter(article_user__user=self.request.user, article_user__like_dislike=False)
        elif 'liked' in self.request.path:
            queryset = Article.objects.filter(article_user__user=self.request.user, article_user__like_dislike=True)
        elif 'recommended' in self.request.path:
            queryset = get_recommended_articles(self.request)
        elif 'recent' in self.request.path:
            queryset = Article.objects.order_by('-date', 'title')
        elif 'popular' in self.request.path:
            queryset = Article.objects.annotate(n_likes=Count(Case(
                When(article_user__like_dislike=True, then=1),
                output_field=IntegerField(),
            ))).order_by('-n_likes', 'title')
        elif 'related' in self.request.path:
            article_id = self.request.query_params.get('id')
            print(article_id, 'article____id')
            article = Article.objects.get(id=article_id)
            queryset = get_related_articles(article)
        elif 'author' in self.request.path:
            author_name = self.request.query_params.get('name')
            author = Author.objects.get(name=author_name)
            queryset = author.articles.order_by('-date')
        else:
            raise Exception('Unknown API link')

        return queryset

    def list(self, request):
        queryset = self.get_queryset()

        page = request.query_params.get('page')
        if page is not None:
            paginate_queryset = self.paginate_queryset(queryset)
            serializer = self.serializer_class(paginate_queryset, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ArticlesShortSerializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, pk=None):
        article = get_object_or_404(Article, id=pk)
        article_user, is_created = ArticleUser.objects.get_or_create(user=request.user, article_id=pk)
        user_tags, _ = UserTags.objects.get_or_create(user=request.user)

        if 'in_lib' in request.data.keys():
            article_user.in_lib = request.data['in_lib']

            if article_user.in_lib and article.has_inner_vector:
                user_tags.tags = RelationModel.add_user_tags(
                    user_tags.tags, user_tags.n_articles,
                    article.articletext.tags, article.articletext.tags_norm  # todo CHECKME
                )
                user_tags.n_articles += 1
                user_tags.save()
            else:
                # todo remove tags, Vladyan!
                pass
        if 'like_dislike' in request.data.keys():
            article_user.like_dislike = request.data['like_dislike']

            if article_user.like_dislike and article.has_inner_vector:
                user_tags, _ = UserTags.objects.get_or_create(user=request.user)
                user_tags.tags = RelationModel.add_user_tags(
                    user_tags.tags, user_tags.n_articles,
                    article.articletext.tags, article.articletext.tags_norm
                )
                user_tags.n_articles += 1
                user_tags.save()
            else:
                # todo remove tags, Vladyan!
                pass

        if 'note' in request.data.keys():
            article_user.note = request.data['note']
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

        return _success()

    def create(self, request):
        print('create', request.user, request.data)
        is_exists = BlogPost.objects.filter(url=request.data['url'], article_id=request.data['article_id']).count() > 0

        if is_exists:
            _error('Blog Post is already attached')

        blogpost = BlogPost.objects.create(
            title=request.data['title'],
            url=request.data['url'],
            article_id=request.data['article_id'],
            who_added=request.user
        )

        blogpost.save()

        return _success()


class GitHubAPI(viewsets.ViewSet):
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = GitHubSerializer
    queryset = GitHubRepository.objects.all()

    # def retrieve(self, request, pk):
    #     repo = GitHubRepository.objects.get(id=pk)
    #     serializer = GitHubSerializer(repo, many=False)
    #     return Response(serializer.data)

    # def list(self, request):
    #     article_id = self.request.query_params.get('article_id')
    #
    #     Response({})

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

        return _success()

    def create(self, request):
        print(request.data)
        url = request.data['url']

        if not GitHubRepo.is_github_repo(url):
            article_id = request.data['article_id']
            is_exists = BlogPost.objects.filter(url=url, article_id=article_id).count() > 0
            if is_exists:
                return _error('The proposed GitHub repository is already attached :-)')

            resource = BlogPost.objects.create(
                url=url,
                article_id=article_id,
                who_added=request.user
            )

            resource.save()

            print('pisya')

            return _success()

        if 'arxiv_id' in request.data.keys():
            arxiv_id = request.data['arxiv_id']
            article_exists = Article.objects.filter(arxiv_id=arxiv_id).count() > 0

            if not article_exists:
                return _error("Article with ArXiv ID %s doesn't exists" % arxiv_id)

            article_id = Article.objects.get(arxiv_id=arxiv_id).id

        else:
            article_id = request.data['article_id']
            is_exists = GitHubRepository.objects.filter(url=url, article_id=article_id).count() > 0

            if is_exists:
                return _error('The proposed GitHub repository is already attached :-)')



        new_git = dict(
            url=url,
            article_id=article_id
        )

        if type(request.user) != AnonymousUser:
            new_git.update({
                'who_added': request.user
            })

        repo = GitHubRepository.objects.create(
            **new_git
        )

        print('PIZDA')

        repo.save()

        return _success()


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

    def get(self, request, keywords_raw=None):
        # read params
        if keywords_raw is None:
            keywords_raw = request.query_params.get('keywords', None)

        if keywords_raw is None:
            data = DefaultStore.objects.get(key='trends').value
            return Response(json.loads(data))

        # check params
        try:
            keywords_names = [kw.strip() for kw in keywords_raw.split(',')]
            keywords = [kw.lower() for kw in keywords_names]
        except Exception:
            return Response(status=400)

        data = []
        for i, k in enumerate(keywords):
            db = NGramsMonth.objects.filter(type=1, sentences__has_key=k)
            for item in db:
                label_code = item.label_code
                data.append({
                    'date': str(label_code // 100) + '/' + str(label_code % 100) + '/1',
                    'key': keywords_names[i],
                    'value': int(item.sentences[k])
                })

        return Response({
            'data': data
        })


class CategoriesAPI(APIView):
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly
    ]

    def get(self, request, categories_raw=None):
        # read params
        if categories_raw is None:
            categories_raw = request.query_params.get('categories', None)

        if categories_raw is None:
            data = DefaultStore.objects.get(key='categories').value
            return Response(json.loads(data))

        # check params
        try:
            categories = [cat.strip() for cat in categories_raw.split(',')]
        except Exception:
            return Response(status=400)

        data = []
        db = Categories.objects.filter(pk__in=categories)
        for item in db.values_list('category', 'category_full', 'months'):
            for date_code in item[2]:
                data.append({
                    'date': date_code[:4] + '/' + date_code[4:] + '/1',
                    'key': item[0] + ': ' + item[1],
                    'value': int(item[2][date_code])
                })

        return Response({
            'data': data
        })



