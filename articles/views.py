import datetime
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, When, Case
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import FormView
from django.views.generic import ListView
from el_pagination.decorators import page_template
from el_pagination.views import AjaxListView
from django.contrib.auth import login

# from core.forms import UserSignUpForm, UserLoginForm
from articles.models import Article, Author, ArticleUser, NGramsSentence, SentenceVSMonth, ArticleArticleRelation, \
    CategoriesVSDate
from search.documents import ArticleDocument
from search.forms import SearchForm
from utils.constants import GLOBAL__COLORS, VISUALIZATION__INITIAL_NUM_BARS, GLOBAL__CATEGORIES
from django_ajax.mixin import AJAXMixin


@login_required(login_url='/accounts/login')
def home(request):
    n_articles = Article.objects.count()

    articles_lib = Article.objects.filter(articleuser__user=request.user, articleuser__in_lib=True)
    n_articles_in_lib = articles_lib.count()

    category_data = json.loads(category_view(request).content)
    trend_data = json.loads(trend_view(request).content)

    context = {
        'n_articles': n_articles,
        'n_articles_in_lib': n_articles_in_lib,
        'stacked_bar_chart': json.dumps(category_data['data']),
        'stacked_bar_chart_full': json.dumps(category_data['data_full']),
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
        categories = list(GLOBAL__CATEGORIES.keys())[:6]

    colors = GLOBAL__COLORS.get_colors_code(len(categories))

    labels, datasets = [], []
    for color, cat in zip(colors, categories):
        data = {
            'label': cat + ': ' + GLOBAL__CATEGORIES[cat],
            'fill': False,
            'backgroundColor': color,
            'borderColor': color
        }

        counts = CategoriesVSDate.objects.filter(from_category=cat).order_by('from_month__date_code')
        data['data'] = list(counts.values_list('count', flat=True))

        if len(labels) == 0:
            labels = list(counts.values_list('from_month__date', flat=True))

        datasets.append(data)

    data = {
        'labels': labels,
        'datasets': datasets
    }
    full_data = {
        'labels': labels,
        'datasets': [x['data'] for x in datasets]
    }

    data['labels'] = full_data['labels'][-VISUALIZATION__INITIAL_NUM_BARS:]
    for x in data['datasets']:
        x['data'] = x['data'][-VISUALIZATION__INITIAL_NUM_BARS:]

    return JsonResponse({
        'data': data,
        'data_full': full_data
    })


@login_required(login_url='/accounts/login')
def trend_view(request, keywords_raw=None):
    if request.method == 'POST':
        keywords_raw = request.POST.get('keywords_raw')
    elif keywords_raw is None:
        keywords_raw = "Machine Learning, Neural Networks, Computer Vision, Deep Learning"

    keywords = [kw.strip() for kw in keywords_raw.split(',')]
    colors = GLOBAL__COLORS.get_colors_code(len(keywords))

    res = {}
    min_tick = 300000
    for kw in keywords:
        res[kw] = {}
        item = NGramsSentence.objects.filter(sentence=kw.lower())
        if item.count() == 0:
            continue
        assert item.count() == 1

        freq = SentenceVSMonth.objects.filter(from_item=item[0]).order_by('from_corpora__label_code')
        freq = list(freq.values_list('freq_text', 'from_corpora__label', 'from_corpora__label_code'))

        for f in freq:
            res[kw][f[1]] = f[0]

        min_tick = min(min_tick, min([x[2] for x in freq]))

    now = datetime.datetime.now()
    if min_tick == 300000:
        min_tick = (now.year - 1) * 100 + now.month

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

    while not (year == now.year and month > now.month):
        label = datetime.date(year, month, 1).strftime('%b %y')
        line_data['labels'].append(label)
        for i, kw in enumerate(keywords):
            if label in res[kw]:
                line_data['datasets'][i]['data'].append(res[kw][label])
            else:
                line_data['datasets'][i]['data'].append(0)

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
            return Article.objects.annotate(n_likes=Count('articleuser__like_dislike')).order_by('-n_likes')

        if current_tab == 'recommended':
            # articles_negative = ArticleUser.objects.filter(user=self.request.user, like_dislike=False).values('article')
            articles_positive = list(ArticleUser.objects.filter(
                Q(like_dislike=True) | Q(in_lib=True),
                user=self.request.user
            ).values_list('article', flat=True))

            if len(articles_positive) == 0:
                return Article.objects.order_by('-date')

            jury = {}
            for art in articles_positive:
                for x in ArticleArticleRelation.objects.filter(left_id=art).values('right_id', 'distance'):
                    key = x['right_id']
                    if key not in articles_positive:
                        if key not in jury:
                            jury[key] = [x['distance']]
                        else:
                            jury[key].append(x['distance'])

            jury = sorted(jury.items(), key=lambda x: min(x[1]))
            ids = [x[0] for x in jury]

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
        return Article.objects.filter(articleuser__user=self.request.user, articleuser__in_lib=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_name'] = 'Library'
        context['page_id'] = 'library'

        return context


class LikedDisliked(ArticlesView, LoginRequiredMixin):
    login_url = '/accounts/login'

    def get_queryset(self):
        liked = 'disliked' not in self.request.get_raw_uri()
        return Article.objects.filter(articleuser__user=self.request.user, articleuser__like_dislike=liked)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        liked = 'disliked' not in self.request.get_raw_uri()
        context['page_name'] = 'Liked' if liked else 'Disliked'
        context['page_id'] = 'liked' if liked else 'disliked'

        return context


class ArticleDetailsView(AjaxListView, ArticlesMixin):
    model = Article

    template_name = 'articles/article_details.html'
    page_template = 'articles/related_articles_page.html'
    context_object_name = 'article'

    def get_queryset(self):
        return get_object_or_404(Article, id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['lib_articles_ids'] = self.lib_ids
        context['like_articles_ids'] = self.like_ids
        context['dislike_articles_ids'] = self.dislike_ids
        context['notes'] = self.notes

        article = get_object_or_404(Article, id=self.kwargs['pk'])

        related_articles = article.related.order_by('related_articles__distance')
        context['related_articles'] = related_articles

        context['page_template'] = 'articles/related_articles_page.html'

        context['page_id'] = 'articles'

        return context


@login_required(login_url='/accounts/login')
def add_remove_from_library(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    article_user, _ = ArticleUser.objects.get_or_create(article=article, user=request.user)

    if request.method == 'POST':
        article_user.in_lib = True
        article_user.save()
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
def like_dislike(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    article_user, _ = ArticleUser.objects.get_or_create(article=article, user=request.user)

    if request.POST['like'] == '1':
        article_user.like_dislike = True
    elif request.POST['like'] == '-1':
        article_user.like_dislike = False
    else:
        article_user.like_dislike = None

    article_user.save()

    return JsonResponse({})


def landing_view(request):
    return render(request, 'landing.html', context={})
