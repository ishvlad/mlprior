import datetime
import json
import pickle

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from el_pagination.decorators import page_template

from articles.documents import ArticleDocument
from articles.forms import UserForm
from articles.models import Article, Author, ArticleUser, NGramsCorporaItem, CorporaItem


@login_required(login_url='/login')
def home(request):
    n_articles = Article.objects.count()

    articles_lib = Article.objects.filter(articleuser__user=request.user, articleuser__in_lib=True)
    n_articles_in_lib = articles_lib.count()

    colors = ["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#dd0000", "#00dd00", "#0000dd"]

    bar_chart_data = pickle.load(open('visualization.pkl', 'rb'))

    full_bar_data = {
        'labels': bar_chart_data['labels'],
        'datasets': [x['data'] for x in bar_chart_data['datasets']]
    }
    bar_chart_data['labels'] = bar_chart_data['labels'][-12:]
    for x in bar_chart_data['datasets']:
        x['data'] = x['data'][-12:]

    keywords = [
        'In this paper',
        'we propose',
        'we assume',
        'we have',
        'qwhdsnjfna'
    ]

    res = {}
    min_tick = 300000
    for kw in keywords:
        res[kw] = {}
        item = NGramsCorporaItem.objects.filter(sentence=kw)
        if item.count() == 0:
            continue
        assert item.count() == 1

        freq = CorporaItem.objects.filter(from_item=item[0]).order_by('from_corpora__label_code')
        freq = list(freq.values_list('freq', 'from_corpora__label', 'from_corpora__label_code'))
        for f in freq:
            res[kw][f[1]] = f[0]

        min_tick = min(min_tick, min([x[2] for x in freq]))

    month = min_tick % 100
    year = min_tick // 100
    now = datetime.datetime.now()

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
    line_data['labels'] = line_data['labels'][-12:]
    for x in line_data['datasets']:
        x['data'] = x['data'][-12:]

    context = {
        'n_articles': n_articles,
        'n_articles_in_lib': n_articles_in_lib,
        'stacked_bar_chart': json.dumps(bar_chart_data),
        'stacked_bar_chart_full': json.dumps(full_bar_data),
        'trend_data': json.dumps(line_data),
        'trend_data_full': json.dumps(full_data)
    }

    return render(request, 'home.html', context)


@page_template('articles_list_page.html')
@login_required(login_url='/login')
def articles(request, template='articles_list.html', extra_context=None):
    all_articles = Article.objects.order_by('-date')

    lib_articles_ids = ArticleUser.objects.filter(user=request.user, in_lib=True).values_list('article', flat=True)

    context = {
        'articles': all_articles,
        'lib_articles_ids': lib_articles_ids,
        'page_name': 'Articles'
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


@page_template('related_articles_page.html')
@login_required(login_url='/login')
def article_details(request, article_id, template='article_details.html', extra_context=None):
    article = get_object_or_404(Article, id=article_id)
    related_articles = article.related.order_by('related_articles__distance')
    lib_articles_ids = ArticleUser.objects.filter(user=request.user, in_lib=True).values_list('article', flat=True)

    context = {
        'article': article,
        'related_articles': related_articles,
        'lib_articles_ids': lib_articles_ids
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


@page_template('articles_list_page.html')
@login_required(login_url='/login')
def author_articles(request, author_name, template='articles_list.html', extra_context=None):
    # all_articles = Article.objects.order_by('-date')

    user = Author.objects.get(name=author_name)
    user_articles = request.user.articles.all()

    context = {
        'articles': user.articles.all(),
        'page_name': 'Articles of %s' % user.name,
        'user_articles': user_articles
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


@login_required(login_url='/login')
def add_remove_from_library(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.method == 'POST':
        ArticleUser.objects.update_or_create(article=article, user=request.user, in_lib=True)
        data = {
            'is_ok': 'ok!'
        }
    elif request.method == 'DELETE':
        ArticleUser.objects.filter(article=article, user=request.user).update(in_lib=False)
        data = {
            'is_ok': 'deleted!'
        }
    else:
        data = {}

    return JsonResponse(data)


@login_required(login_url='/login')
def change_note(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    print('Current notes', article.note)

    if request.method == 'POST':
        print(request.POST.get('note', ''))
        article.note = request.POST.get('note', '')
        article.save()

    data = {
        'is_ok': 'deleted!'
    }

    return JsonResponse(data)


@page_template('articles_list_page.html')
@login_required(login_url='/login')
def search(request, search_query, template='articles_list.html', extra_context=None):
    print('SEARCH!!!')
    s = ArticleDocument.search().query("match", title=search_query)

    for art in s:
        print(art)

    user_articles = request.user.articles.all()

    context = {
        'articles': s.to_queryset(),
        'user_articles': user_articles,
        'page_name': 'Articles',
        'is_lib': False
    }

    if extra_context is not None:
        context.update(extra_context)

    rendered_template = render(request, template, context)
    return HttpResponse(rendered_template, content_type='text/html')


@page_template('articles_list_page.html')
@login_required(login_url='/login')
def library(request, template='articles_list.html', extra_context=None):
    all_articles = Article.objects.filter(articleuser__user=request.user, articleuser__in_lib=True)

    context = {
        'articles': all_articles,
        'page_name': 'Library',
        'is_lib': True
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


def register(request):
    user_form = UserForm()
    return render(request, 'register.html', {
        'user_form': user_form
    })
