import datetime
import json
import numpy as np

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, When, Case
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import CreateView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django_ajax.mixin import AJAXMixin
from el_pagination.views import AjaxListView

from articles.forms import AddBlogPostForm
from articles.models import Article, Author, ArticleUser, UserTags, \
    CategoriesVSDate, CategoriesDate, BlogPostUser, BlogPost, GitHubRepository, NGramsMonth
from core.views import AjaxableResponseMixin
from search.forms import SearchForm
from utils.constants import GLOBAL__COLORS, VISUALIZATION__INITIAL_NUM_BARS, GLOBAL__CATEGORIES
from utils.recommendation import RelationModel

@login_required(login_url='/accounts/login')
def home(request):
    n_articles = Article.objects.count()

    articles_lib = Article.objects.filter(article_user__user=request.user, article_user__in_lib=True)
    n_articles_in_lib = articles_lib.count()

    n_blog_posts = BlogPost.objects.count()
    n_github_repos = GitHubRepository.objects.count()

    category_data = json.loads(category_view(request).content)
    trend_data = json.loads(trend_view(request).content)

    context = {
        'n_articles': n_articles,
        'n_articles_in_lib': n_articles_in_lib,
        'n_blog_posts': n_blog_posts,
        'n_githubs': n_github_repos,
        'stacked_bar_chart': json.dumps(category_data),
        'trend_data': json.dumps(trend_data['data']),
        'trend_data_full': json.dumps(trend_data['data_full']),
        'keywords_raw': "Machine Learning, Neural Networks, Computer Vision, Deep Learning",
        'page_id': 'home'
    }

    return render(request, 'home.html', context)


@login_required(login_url='/accounts/login')
def category_view(request, categories=None):
    if request.method == 'POST':
        categories = request.POST.get('categories')
    elif categories is None:
        categories = [c for c in GLOBAL__CATEGORIES.keys() if c.startswith('cs.')][:4]

    colors = GLOBAL__COLORS.get_colors_code(len(categories))
    dates = list(CategoriesDate.objects.filter(date_code__gte=200000).order_by('date_code').values_list('date', flat=True))

    def insert(arr):
        if int(arr[1]) > 50:
            return arr[0] + ' 19' + arr[1]
        else:
            return arr[0] + ' 20' + arr[1]

    dates = [insert(d.split(' ')) for d in dates]
    names = [c + ': ' + GLOBAL__CATEGORIES[c] for c in categories]

    datasets = []
    for cat in categories:
        counts = CategoriesVSDate.objects.filter(from_category=cat, from_month__date_code__gte=200000).order_by('from_month__date_code')
        datasets.append(list(counts.values_list('count', flat=True)))

    for i in range(len(datasets)):
        if len(datasets[i]) == 0:
            datasets[i] = [0]*len(dates)

    return JsonResponse({
        'colors': colors,
        'names': names,
        'dates': dates,
        'data': datasets
    })


@login_required(login_url='/accounts/login')
def trend_view(request, keywords_raw=None):

    if request.method == 'POST':
        keywords_raw = request.POST.get('keywords_raw')
    elif keywords_raw is None:
        keywords_raw = "Machine Learning, Neural Networks, Computer Vision, Deep Learning"

    keywords = [kw.strip().lower() for kw in keywords_raw.split(',')]
    colors = GLOBAL__COLORS.get_colors_code(len(keywords))

    items = NGramsMonth.objects.filter(type=1, sentences__has_any_keys=keywords).order_by('label_code')
    items = items.values('label_code', 'label', 'sentences')

    now = datetime.datetime.now()
    min_tick = (now.year - 1) * 100 + now.month

    if items.count() != 0:
        min_tick = min(items[0]['label_code'], min_tick)

    month = min_tick % 100
    year = min_tick // 100

    line_data = {
        'labels': [],
        'datasets': [{
            'label': k,
            'fill': False,
            'backgroundColor': c,
            'borderColor': c,
            'data': []
        } for k, c in zip(keywords, colors)]
    }

    count = 0
    while not ((year == now.year and month > now.month) or year > now.year):
        label = datetime.date(year, month, 1).strftime('%b %y')
        line_data['labels'].append(label)

        if items.count() == count or items[count]['label'] != label:
            for i, kw in enumerate(keywords):
                line_data['datasets'][i]['data'].append(0)
        else:
            for i, kw in enumerate(keywords):
                if kw in items[count]['sentences']:
                    line_data['datasets'][i]['data'].append(int(items[count]['sentences'][kw]))
                else:
                    line_data['datasets'][i]['data'].append(0)
            count += 1

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    full_data = {
        'labels': line_data['labels'],
        'datasets': [x['data'] for x in line_data['datasets']]
    }
    line_data['labels'] = line_data['labels'][-VISUALIZATION__INITIAL_NUM_BARS:]
    for x in line_data['datasets']:
        x['data'] = x['data'][-VISUALIZATION__INITIAL_NUM_BARS:]

    return JsonResponse({
        'data': line_data,
        'data_full': full_data
    })


class ArticlesMixin(object):
    @property
    def like_ids(self):
        article_user = ArticleUser.objects.filter(user=self.request.user, like_dislike=True)
        return article_user.values_list('article', flat=True)

    @property
    def blog_posts_like_ids(self):
        blog_post_user = BlogPostUser.objects.filter(user=self.request.user, is_like=True)
        print(blog_post_user)
        return blog_post_user.values_list('blog_post', flat=True)

    @property
    def dislike_ids(self):
        article_user = ArticleUser.objects.filter(user=self.request.user, like_dislike=False)
        return article_user.values_list('article', flat=True)

    @property
    def lib_ids(self):
        article_user = ArticleUser.objects.filter(user=self.request.user, in_lib=True)
        return article_user.values_list('article', flat=True)

    @property
    def notes(self):
        article_user = ArticleUser.objects.filter(user=self.request.user, note__isnull=False)
        return dict(article_user.values_list('article', 'note'))

    @property
    def categories(self):
        cats = list(Article.objects.all().values_list('category'))
        return list(sorted(list(set(cats))))  # OMG LOL KEK


class ArticlesView(ListView, AjaxListView, LoginRequiredMixin, ArticlesMixin, AJAXMixin):
    login_url = '/accounts/login'
    template_name = 'articles/articles_list.html'
    page_template = 'articles/articles_list_page.html'
    model = Article
    context_object_name = 'articles'
    form = SearchForm

    @property
    def tab(self):
        if 'recent' in self.request.get_raw_uri():
            current_tab = 'recent'
        elif 'recommended' in self.request.get_raw_uri():
            current_tab = 'recommended'
        elif 'popular' in self.request.get_raw_uri():
            current_tab = 'popular'
        else:
            current_tab = 'other'

        return current_tab

    def get_queryset(self):
        current_tab = self.tab

        if current_tab == 'recent':
            return Article.objects.order_by('-date')

        if current_tab == 'popular':
            # todo fix
            return Article.objects.annotate(n_likes=Count('article_user__like_dislike')).order_by('-n_likes')

        if current_tab == 'recommended':
            articles_positive = ArticleUser.objects.filter(
                Q(like_dislike=True) | Q(in_lib=True),
                user=self.request.user, article__has_neighbors=True
            )

            # no saved or liked articles
            if articles_positive.count() == 0:
                return []

            # get IDs from seen articles
            viewed_articles_id = ArticleUser.objects.filter(
                Q(like_dislike=True) | Q(like_dislike=False) | Q(in_lib=True),
                user=self.request.user
            ).values_list('id', flat=True)

            # get relations from 100 last liked articles
            relations = articles_positive.order_by('-id')[:100].values('article__articletext__relations')

            # get 1k nearest articles from each relation
            result = {}
            n_result = 10
            for relation in relations:
                relation = relation['article__articletext__relations']
                relation = sorted(relation.items(), key=lambda x: x[1])

                # collect in 'result' all relations with min distance
                count = 0
                for k, v in relation:
                    if int(k) not in viewed_articles_id:
                        if k not in result:
                            result[k] = v
                        elif v < result[k]:
                            result[k] = v

                        count += 1
                        if count > n_result:
                            break

            # (very rare case) -- user disliked all articles in DB except of one (which is saved or liked)
            if len(result) == 0:
                return []

            # get nearest 'n_result' articles from 'result'
            result = sorted(result.items(), key=lambda x: x[1])[:n_result]

            # get sorted ids, create order for Django and order resulting articles
            ids = [int(x[0]) for x in result]
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
            queryset = Article.objects.filter(pk__in=ids).order_by(preserved)

            return queryset

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        context['lib_articles_ids'] = self.lib_ids
        context['like_articles_ids'] = self.like_ids
        context['dislike_articles_ids'] = self.dislike_ids
        context['notes'] = self.notes

        context['page_name'] = 'Articles'
        context['page_template'] = 'articles/articles_list_page.html'

        context['tab'] = self.tab

        context['page_id'] = 'articles'
        context['is_authorised'] = self.request.user.is_authenticated

        return context


class ArticlesOfAuthor(ArticlesView):
    template_name = 'articles/author_details.html'

    def get_queryset(self):
        author = Author.objects.get(name=self.kwargs['author_name'])

        return author.articles.order_by('-date')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        author = Author.objects.get(name=self.kwargs['author_name'])
        context['page_name'] = '%s' % author.name

        n_articles = author.articles.count()
        context['n_articles'] = n_articles

        return context


class ArticlesLibrary(ArticlesView, LoginRequiredMixin):
    login_url = '/accounts/login'

    def get_queryset(self):
        return Article.objects.filter(article_user__user=self.request.user, article_user__in_lib=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_name'] = 'Library'
        context['page_id'] = 'library'

        return context


class LikedDisliked(ArticlesView, LoginRequiredMixin):
    login_url = '/accounts/login'

    def get_queryset(self):
        liked = 'disliked' not in self.request.get_raw_uri()
        return Article.objects.filter(article_user__user=self.request.user, article_user__like_dislike=liked)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        liked = 'disliked' not in self.request.get_raw_uri()
        context['page_name'] = 'Liked' if liked else 'Disliked'
        context['page_id'] = 'liked' if liked else 'disliked'

        return context


class ArticleDetailsView(AjaxListView, ArticlesMixin, LoginRequiredMixin, FormView):
    model = Article
    login_url = '/accounts/login'

    form_class = AddBlogPostForm

    template_name = 'articles/article_details.html'
    page_template = 'articles/related_articles_page.html'
    context_object_name = 'article'

    def get_queryset(self):
        return get_object_or_404(Article, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        article = get_object_or_404(Article, id=self.kwargs['pk'])

        articles = Article.objects.filter(articletext__relations__has_key=str(self.kwargs['pk']))
        if articles.count() == 0:
            related_articles = []
        else:
            distance = 'articletext__relations__' + str(self.kwargs['pk'])
            related_articles = articles.order_by(distance)

        context['related_articles'] = related_articles
        context['page_template'] = 'articles/related_articles_page.html'
        context['page_id'] = 'articles'
        context['is_authorised'] = self.request.user.is_authenticated
        context['form'] = AddBlogPostForm()

        if self.request.user.is_anonymous:
            context['is_authorised'] = False
            return context

        context['lib_articles_ids'] = self.lib_ids
        context['like_articles_ids'] = self.like_ids
        context['dislike_articles_ids'] = self.dislike_ids
        context['notes'] = self.notes
        print(self.blog_posts_like_ids)
        # context['blogposts'] = article.blog_post.all()
        context['like_blog_posts_ids'] = self.blog_posts_like_ids

        return context

    def form_valid(self, form):
        print(form)
        return HttpResponseRedirect(self.request.path_info)


class BlogPostCreate(AjaxableResponseMixin, CreateView):
    model = BlogPost
    fields = ['title', 'url']

    def form_valid(self, form):
        # self.success_url = self.request.path_info
        form.instance.article_id = self.request.POST['article_id']
        return super().form_valid(form)


@login_required(login_url='/accounts/login')
def add_remove_from_library(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    article_user, _ = ArticleUser.objects.get_or_create(article=article, user=request.user)
    user_tags, _ = UserTags.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        article_user.in_lib = True
        article_user.save()

        user_tags.tags = RelationModel.add_user_tags(
            user_tags.tags, user_tags.n_articles,
            article.articletext.tags, article.articletext.tags_norm
        )
        user_tags.n_articles += 1
        user_tags.save()
    elif request.method == 'DELETE':
        article_user.in_lib = False
        article_user.save()

    return JsonResponse({})


@login_required(login_url='/accounts/login')
def change_note(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    # print('Current notes', article.note)

    if request.method == 'POST':
        print(request.POST.get('note', ''))

        article_user, _ = ArticleUser.objects.get_or_create(article=article, user=request.user)
        print(article_user)
        article_user.note = request.POST.get('note', '')
        article_user.save()

    return JsonResponse({})


@login_required(login_url='/accounts/login')
def like_dislike_blogpost(request, blogpost_id):
    blogpost = get_object_or_404(BlogPost, id=blogpost_id)
    blogpost_user, _ = BlogPostUser.objects.get_or_create(blog_post=blogpost, user=request.user)

    if request.POST['like'] == '1':
        blogpost_user.is_like = True
        blogpost.rating += 1
    else:
        blogpost_user.is_like = False
        blogpost.rating -= 1

    blogpost_user.save()
    blogpost.save()

    return JsonResponse({})


@login_required(login_url='/accounts/login')
def like_dislike(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    article_user, _ = ArticleUser.objects.get_or_create(article=article, user=request.user)

    if request.POST['like'] == '1':
        article_user.like_dislike = True

        if article.has_inner_vector:
            user_tags, _ = UserTags.objects.get_or_create(user=request.user)
            user_tags.tags = RelationModel.add_user_tags(
                user_tags.tags, user_tags.n_articles,
                article.articletext.tags, article.articletext.tags_norm
            )
            user_tags.n_articles += 1
            user_tags.save()
    elif request.POST['like'] == '-1':
        article_user.like_dislike = False
    else:
        article_user.like_dislike = None

    article_user.save()

    return JsonResponse({})
