import operator
import os
import re
import sys
import tqdm

sys.path.append('./')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import django
django.setup()

import datetime
import pickle
import pandas as pd
from django.db.models.functions import TruncMonth
from nltk import ngrams
from time import time

from articles.models import Article


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
    ##########################################################
    ### If it is not the first start, you have to clear table:
    ### python manage.py dbshell
    ### DELETE FROM articles_articlearticlerelation;
    ### .exit 0
    ##########################################################

    print('START stacked bar chart', end=' ')
    ###############
    ### Stacked Bar
    ###############
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

    huge_store = {}
    grouped = sorted(articles.groupby('idx_sort'), key=operator.itemgetter(0))

    for date, df_group in tqdm.tqdm(grouped):
        key = datetime.date(date // 100, date % 100, 1).strftime('%b %y')
        huge_store[key] = get_grams_dict(df_group.abstract.values)

    print('OK')
    ##########
    ### Saving
    ##########
    print('START Saving')
    pickle.dump((bar_chart_data, huge_store), open('visualization.pkl', 'wb+'))



if __name__ == '__main__':
    total_start_time = time()
    main()

    print('FINISH Total Time, min:', (time() - total_start_time) / 60)
