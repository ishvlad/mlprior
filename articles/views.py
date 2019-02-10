import re
import json
import operator
import datetime
import pandas as pd
from nltk import ngrams


from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from el_pagination.decorators import page_template

from articles.documents import ArticleDocument
from articles.forms import UserForm
from articles.models import Article, Author, ArticleUser


@login_required(login_url='/login')
def home(request):
    n_articles = Article.objects.count()

    articles_lib = Article.objects.filter(articleuser__user=request.user, articleuser__in_lib=True)
    n_articles_in_lib = articles_lib.count()

    categories = ['cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.ML', 'cs.NE']
    colors = ["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#dd0000", "#00dd00", "#0000dd"]

    bar_chart_data = {
        'labels': [],
        'datasets': []
    }
    for cat, color in zip(categories, colors):
        bar_chart_data['datasets'].append({
            'label': cat,
            'backgroundColor': color,
            'data': []
        })


    ##########################
    ### Should be preprocessed
    ##########################

    counts_for_bar = list(Article.objects.all().annotate(month=TruncMonth('date')).values('month', 'category'))
    df = pd.DataFrame(counts_for_bar, columns=['category', 'month'])
    df = df[(df.category == 'cs.CV') | (df.category == 'cs.AI') | (df.category == 'cs.LG') | \
            (df.category == 'cs.CL') | (df.category == 'cs.NE') | (df.category == 'cs.ML')]
    df.sort_values('month', inplace=True)

    for month, df_group in df.groupby(['month']):
        if month.year > 2017:
            bar_chart_data['labels'].append(month.strftime('%b %y'))
            for i, cat in enumerate(categories):
                bar_chart_data['datasets'][i]['data'].append(
                    sum(df_group.category == cat)
                )

    #################################
    ### END OF Should be preprocessed
    #################################

    keywords = [
        # 'Supervised', 'Unsupervised', 'Reinforcement',
        'we propose',
        'we assume',
        'we show',
        'we present'
        # 'Generative Adversarial Networks',
        # 'Recurrent Neural Networks',
        # 'Convolutional Neural Networks',
        # 'Graph Neural Networks',
        # 'GPU', 'CPU'
    ]
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

    start_date = 201500

    ##########################
    ### Should be preprocessed
    ##########################

    def get_grams_dict(sentences, max_ngram_len = 4):
        # stop_words = [
        #     'a', 'the', 'in', 'of', 'in', 'this', 'and',
        #     'to', 'we', 'for', 'is', 'that', 'on', 'with'
        #     'are', 'by', 'as', 'an', 'from', 'our', 'be'
        # ]

        p = re.compile('\w+[\-\w+]*', re.IGNORECASE)
        dic = [{} for _ in range(max_ngram_len)]

        for n in range(1, max_ngram_len + 1):
            for s in sentences:
                grams = ngrams(p.findall(s.lower()), n)

                for key in set(grams):
                    # miss = False
                    # for sw in stop_words:
                    #     if sw in key:
                    #         miss = True
                    #         break
                    # if miss:
                    #     continue

                    key = ' '.join(key)
                    if key in dic[n - 1]:
                        dic[n - 1][key] += 1
                    else:
                        dic[n - 1][key] = 1

        return dic

    articles = pd.DataFrame(Article.objects.all().values())
    articles['date'] = pd.to_datetime(articles['date'])
    articles['idx_sort'] = articles.date.dt.month + articles.date.dt.year * 100
    articles.sort_values('idx_sort', inplace=True)

    grouped = articles[articles.idx_sort > start_date].groupby('idx_sort')
    for d, df_group in sorted(grouped, key=operator.itemgetter(0)):
        line_data['labels'].append(datetime.date(d // 100, d % 100, 1).strftime('%b %y'))

        dics = get_grams_dict(df_group.abstract.values)

        for i, kw in enumerate(keywords):
            idx = len(kw.split()) - 1
            kw = kw.lower()
            if kw in dics[idx]:
                line_data['datasets'][i]['data'].append(dics[idx][kw])
            else:
                line_data['datasets'][i]['data'].append(0)

    full_data = {
        'labels': line_data['labels'],
        'datasets': [x['data'] for x in line_data['datasets']]
    }
    line_data['labels'] = line_data['labels'][-12:]
    for x in line_data['datasets']:
        x['data'] = x['data'][-12:]


    #################################
    ### END OF Should be preprocessed
    #################################

    context = {
        'n_articles': n_articles,
        'n_articles_in_lib': n_articles_in_lib,
        'stacked_bar_chart': json.dumps(bar_chart_data),
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
    related_articles = article.related.order_by('related__from_article__distance')
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
