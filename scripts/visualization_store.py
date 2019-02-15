##########################################################
### If it is not the first start, you have to clear table:
### python manage.py dbshell
### DELETE FROM articles_ngramscorporabymonth;
### DELETE FROM articles_ngramscorporaitem;
### DELETE FROM articles_corporaitem;
### .exit 0
##########################################################

import datetime
import operator
import os
import pickle
import re
import sys
import tqdm

sys.path.append('./')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import django

django.setup()

import pandas as pd
from django.db.models.functions import TruncMonth
from nltk import ngrams
from time import time

from articles.models import Article, NGramsCorporaByMonth, NGramsCorporaItem, CorporaItem
from scripts.arxiv_retreive import DBManager
from utils.constants import GLOBAL__COLORS, GLOBAL__CATEGORIES


def get_grams_dict(sentences, max_ngram_len=5):
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


def main():
    print('START stacked bar chart', end=' ')
    ###############
    ### Stacked Bar
    ###############
    categories = list(GLOBAL__CATEGORIES.keys())[:8]
    colors = GLOBAL__COLORS.get_colors_code(len(categories))
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

    articles = Article.objects.all()
    counts_for_bar = list(articles.annotate(month=TruncMonth('date')).values('month', 'category'))
    df = pd.DataFrame(counts_for_bar, columns=['category', 'month'])

    idx = df.category == categories[0]
    for cat in categories[1:]:
        idx |= df.category == cat
    df = df[idx]
    df.sort_values('month', inplace=True)

    store = {}
    for date, df_group in df.groupby(['month']):
        store[date.month + date.year * 100] = df_group

    month = min(store) % 100
    year = min(store) // 100
    now = datetime.datetime.now()

    while not (year == now.year and month > now.month):
        date = datetime.date(year, month, 1).strftime('%b %y')
        bar_chart_data['labels'].append(date)

        key = month + year * 100
        if key in store:
            for i, cat in enumerate(categories):
                bar_chart_data['datasets'][i]['data'].append(
                    sum(store[key].category == cat)
                )
        else:
            for i in range(len(categories)):
                bar_chart_data['datasets'][i]['data'].append(0)

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    print('OK')
    ###############
    ### Trend Lines
    ###############
    print('START Trend lines')

    articles = pd.DataFrame(articles.values())
    articles['date'] = pd.to_datetime(articles['date'])
    articles['idx_sort'] = articles.date.dt.month + articles.date.dt.year * 100
    articles.sort_values('idx_sort', inplace=True)

    max_n_for_grams = 5
    month = min(articles.idx_sort) % 100
    year = min(articles.idx_sort) // 100

    corpora = []
    while not (year == now.year and month > now.month):
        label = datetime.date(year, month, 1).strftime('%b %y')
        label_code = month + year * 100

        for i in range(1, max_n_for_grams + 1):
            corpora.extend([NGramsCorporaByMonth(
                length=i, label=label, label_code=label_code
            )])

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    dics = get_grams_dict(articles.abstract.values, max_n_for_grams)
    items = []
    for d in dics:
        items.extend([NGramsCorporaItem(sentence=s) for s in d])

    db = DBManager()
    db.create_ngram_item(items)
    db.create_ngram_corpora(corpora)

    links = []
    grouped = sorted(articles.groupby('idx_sort'), key=operator.itemgetter(0))
    for date, df_group in tqdm.tqdm(grouped):
        dics = get_grams_dict(df_group.abstract.values, max_n_for_grams)

        for i, dic in enumerate(dics):
            corpora = NGramsCorporaByMonth.objects.filter(label_code=date, length=i + 1)
            if len(corpora) == 0:
                continue
            assert len(corpora) == 1
            corpus = corpora[0]

            for key in dic:
                item = NGramsCorporaItem.objects.filter(sentence=key)
                assert len(item) == 1
                item = item[0]

                links.append(CorporaItem(
                    freq=dic[key],
                    from_corpora=corpus,
                    from_item=item
                ))

    db.create_corpora_item_link(links)
    print('OK')
    ##########
    ### Saving
    ##########
    print('START Saving')
    pickle.dump(bar_chart_data, open('visualization.pkl', 'wb+'))


if __name__ == '__main__':
    total_start_time = time()
    main()

    print('FINISH Total Time, min:', (time() - total_start_time) / 60)
