import os
import sys
import tqdm

sys.path.append('./')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer, HashingVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.neighbors import NearestNeighbors
from time import time

import django
django.setup()

from articles.models import Article, ArticleArticleRelation
from scripts.arxiv_retreive import DBManager


def get_features(articles):
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=40)
    title_tfidf = vectorizer.fit_transform(articles.title.values).toarray()

    vectorizer = HashingVectorizer(ngram_range=(1, 3), n_features=40)
    title_hash = vectorizer.fit_transform(articles.title.values).toarray()

    encoder = OneHotEncoder(n_values=len(set(articles.category.values)), categories='auto', sparse=False)
    category_onehot = encoder.fit_transform(articles.category.values.reshape(-1, 1))

    features = [
        title_tfidf,
        title_hash,
        category_onehot,
        articles.version.values.astype(int).reshape(-1, 1)
    ]
    all_features = StandardScaler().fit_transform(np.hstack(features))

    return all_features


def get_knn_list(features, n_neighbors=200):
    knn = NearestNeighbors()
    knn.fit(features)

    dists, nn = knn.kneighbors(features, n_neighbors)
    result = np.vstack([
        [(i, idx_r, d) for d, idx_r in zip(dists[i][1:], nn[i][1:])] for i in range(len(dists))
    ])

    return result


def main():
    ##########################################################
    ### If it is not the first start, you have to clear table:
    ### python manage.py dbshell
    ### DELETE FROM articles_articlearticlerelation;
    ### .exit 0
    ##########################################################

    print('START loading articles', end=' ')
    articles = pd.DataFrame(Article.objects.all().values('id','title', 'category', 'version', 'date'))
    print('OK')

    print('START feature engineering', end=' ')
    features = get_features(articles)
    print('OK')

    n_neighbors = 20
    print('START obtain ' + str(n_neighbors) + ' neighbors', end=' ')
    sys.stdout.flush()
    knn_list = get_knn_list(features, n_neighbors)
    print('OK')

    print('START Saving (len: %d)' % len(knn_list))
    items = []
    ids_left, ids_right = knn_list[:, 0].astype(int), knn_list[:, 1].astype(int)
    ids_left, ids_right = articles.loc[ids_left].id.values, articles.loc[ids_right].id.values
    for i_left, i_right, distance in tqdm.tqdm(zip(ids_left, ids_right, knn_list[:, 2])):
        items.append(ArticleArticleRelation(
            left_id=i_left,
            right_id=i_right,
            distance=distance
        ))
    db = DBManager()
    db.create_articles_relation(items)


if __name__ == '__main__':
    total_start_time = time()
    main()

    print('FINISH Total Time, min:', (time() - total_start_time) / 60)
