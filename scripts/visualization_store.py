##########################################################
### If it is not the first start, you have to clear table:
# python manage.py dbshell
# DELETE FROM articles_ngramsmonth;
# DELETE FROM articles_ngramssentence;
# DELETE FROM articles_sentencevsmonth;
# DELETE FROM articles_categories;
# DELETE FROM articles_categoriesdate;
# DELETE FROM articles_categoriesvsdate;
# .exit 0
##########################################################

import datetime
import operator
import os
import re
import sys
import tqdm

sys.path.append('./')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import django

django.setup()

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.db.models import Min
from django.db.models.functions import TruncMonth
from nltk import ngrams
from time import time

from articles.models import Article, NGramsMonth, NGramsSentence, SentenceVSMonth, \
    Categories, CategoriesDate, CategoriesVSDate
from scripts.db_manager import DBManager
from utils.constants import GLOBAL__CATEGORIES


def get_grams_dict(sentences, max_ngram_len=5):
    # stop_words = [
    #     'a', 'the', 'in', 'of', 'in', 'this', 'and',
    #     'to', 'we', 'for', 'is', 'that', 'on', 'with'
    #     'are', 'by', 'as', 'an', 'from', 'our', 'be'
    # ]

    p = re.compile('\w+[\-\w+]*', re.IGNORECASE)
    dic = [{} for _ in range(max_ngram_len)]

    key_store = []

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
                key_store.append(key)

    return dic, key_store


def main():
    print('START stacked bar chart', end=' ')
    #############
    # Stacked Bar
    #############
    categories = [Categories(
        category=k,
        category_full=v
    ) for k, v in GLOBAL__CATEGORIES.items()]

    m_date = Article.objects.all().aggregate(Min('date'))['date__min']
    m_date = datetime.date(year=m_date.year, month=m_date.month, day=1)
    now = datetime.datetime.now().date()

    dates = []

    while m_date <= now:
        dates.append(CategoriesDate(
            date_code=m_date.month + m_date.year * 100,
            date=m_date.strftime('%b %y')
        ))

        m_date += relativedelta(months=1)

    db = DBManager()
    db.bulk_create(Categories, categories)
    db.bulk_create(CategoriesDate, dates)

    articles = Article.objects.all().annotate(month=TruncMonth('date'))
    sub_articles = articles.values('month', 'category')

    cat_vs_date = []
    for cat in categories:
        for d in dates:
            dt = datetime.date(year=d.date_code // 100, month=d.date_code % 100, day=1)
            cat_vs_date.append(CategoriesVSDate(
                from_category=cat,
                from_month=d,
                count=sub_articles.filter(category=cat.category, month=dt).count()
            ))

    db.bulk_create(CategoriesVSDate, cat_vs_date)

    print('OK')
    #############
    # Trend Lines
    #############
    print('START Trend lines')

    articles = pd.DataFrame(Article.objects.values('date', 'title', 'abstract', 'articletext__text'))
    articles['date'] = pd.to_datetime(articles['date'])
    articles['idx_sort'] = articles.date.dt.month + articles.date.dt.year * 100
    articles.sort_values('idx_sort', inplace=True)

    max_n_for_grams = 3
    month = min(articles.idx_sort) % 100
    year = min(articles.idx_sort) // 100

    corpora = []
    while not (year == now.year and month > now.month):
        label = datetime.date(year, month, 1).strftime('%b %y')
        label_code = month + year * 100

        for i in range(1, max_n_for_grams + 1):
            corpora.extend([NGramsMonth(
                length=i, label=label, label_code=label_code
            )])

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    dics_title, keys_title = get_grams_dict(articles.title.values, max_n_for_grams)
    print('Found %d Ngrams in Title' % len(keys_title))
    dics_abstract, keys_abstract = get_grams_dict(articles.abstract.values, max_n_for_grams)
    print('Found %d Ngrams in Abstract' % len(keys_abstract))
    dics_text, keys_text = get_grams_dict(articles.articletext__text.values, max_n_for_grams)
    print('Found %d Ngrams in Text' % len(keys_text))

    print('START Saving sentences in DB')
    db = DBManager()
    db.bulk_create(NGramsMonth, corpora)
    batch_size = 1000
    batch = []
    for s in tqdm.tqdm(set(keys_title + keys_abstract + keys_text)):
        batch.append(NGramsSentence(sentence=s))
        if len(batch) == batch_size:
            db.bulk_create(NGramsSentence, batch)
            batch = []
    if len(batch) != 0:
        db.bulk_create(NGramsSentence, batch)
    print('Now filling')

    links = {}
    grouped = sorted(articles.groupby('idx_sort'), key=operator.itemgetter(0))
    for date, df_group in tqdm.tqdm(grouped):
        dics_title, _ = get_grams_dict(df_group.title.values, max_n_for_grams)
        dics_abstract, _ = get_grams_dict(df_group.abstract.values, max_n_for_grams)
        dics_text, _ = get_grams_dict(df_group.articletext__text.values, max_n_for_grams)

        for i in range(1, max_n_for_grams+1):
            corpus = NGramsMonth.objects.filter(label_code=date, length=i)[0]

            for key in dics_title[i-1]:
                item = NGramsSentence.objects.filter(sentence=key)[0]

                links[(key, date)] = {
                    'freq_title': dics_title[i-1][key],
                    'freq_abstract': 0,
                    'freq_text': 0,
                    'from_corpora': corpus,
                    'from_item': item
                }

            for key in dics_abstract[i-1]:
                if (key, date) in links:
                    links[(key, date)]['freq_abstract'] = dics_abstract[i-1][key]
                else:
                    item = NGramsSentence.objects.filter(sentence=key)[0]

                    links[(key, date)] = {
                        'freq_title': 0,
                        'freq_abstract': dics_abstract[i-1][key],
                        'freq_text': 0,
                        'from_corpora': corpus,
                        'from_item': item
                    }

            for key in dics_text[i-1]:
                if (key, date) in links:
                    links[(key, date)]['freq_text'] = dics_text[i-1][key]
                else:
                    item = NGramsSentence.objects.filter(sentence=key)[0]

                    links[(key, date)] = {
                        'freq_title': 0,
                        'freq_abstract': 0,
                        'freq_text': dics_text[i-1][key],
                        'from_corpora': corpus,
                        'from_item': item
                    }

    print('Filling %d sentences-months OK' % len(links))

    ########
    # Saving
    ########
    print('START Saving %d items' % len(links))
    batch_size = 1000
    batch = []
    for v in tqdm.tqdm(links.values()):
        batch.append(SentenceVSMonth(
            from_corpora=v['from_corpora'],
            from_item=v['from_item'],
            freq_title=v['freq_title'],
            freq_abstract=v['freq_abstract'],
            freq_text=v['freq_text']
        ))
        if len(batch) == batch_size:
            db.bulk_create(SentenceVSMonth, batch)
            batch = []
    if len(batch) != 0:
        db.bulk_create(SentenceVSMonth, batch)


if __name__ == '__main__':
    total_start_time = time()
    main()

    print('FINISH Total Time, min:', (time() - total_start_time) / 60)
