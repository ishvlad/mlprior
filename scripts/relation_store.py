##########################################################
### If it is not the first start, you have to clear table:
### python manage.py dbshell
### DELETE FROM articles_articlearticlerelation;
### DELETE FROM articles_articlevector;
### .exit 0
##########################################################

import os
import sys
import tqdm

sys.path.append('./')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from time import time

import django
django.setup()

from articles.models import Article, ArticleArticleRelation, ArticleVector
from scripts.arxiv_retreive import DBManager


def get_features(articles):
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=20,
                                 encoding='utf-8', decode_error='replace', strip_accents='unicode',
                                 lowercase=True, analyzer='word', stop_words='english')
    title_tfidf = vectorizer.fit_transform(articles.title.values).toarray()

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=50,
                                 encoding='utf-8', decode_error='replace', strip_accents='unicode',
                                 lowercase=True, analyzer='word', stop_words='english')
    abstract_tfidf = vectorizer.fit_transform(articles.abstract.values).toarray()

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=230,
                                 encoding='utf-8', decode_error='replace', strip_accents='unicode',
                                 lowercase=True, analyzer='word', stop_words='english')
    text_tfidf = vectorizer.fit_transform(articles.articletext__text.values).toarray()

    features = [
        title_tfidf,
        abstract_tfidf,
        text_tfidf
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
    print('START loading articles', end=' ')
    articles = pd.DataFrame(Article.objects.values('id', 'title', 'abstract', 'articletext__text'))
    print('OK')

    print('START feature engineering', end=' ')
    features = get_features(articles)
    print('OK')

    n_neighbors = 20
    print('START obtain ' + str(n_neighbors) + ' neighbors', end=' ')
    sys.stdout.flush()
    knn_list = get_knn_list(features, n_neighbors)
    print('OK')

    db = DBManager()
    print('START Saving vectors (len: %d)' % len(features))
    items = []
    for idx, feature in zip(articles.id.values, features):
        items.append(ArticleVector(
            article_origin_id=idx,
            inner_vector=feature
        ))
    db.create_articles_vectors(items)

    print('START Saving relations (len: %d)' % len(knn_list))
    items = []
    ids_left, ids_right = knn_list[:, 0].astype(int), knn_list[:, 1].astype(int)
    ids_left, ids_right = articles.loc[ids_left].id.values, articles.loc[ids_right].id.values
    for i_left, i_right, distance in tqdm.tqdm(zip(ids_left, ids_right, knn_list[:, 2])):
        items.append(ArticleArticleRelation(
            left_id=i_left,
            right_id=i_right,
            distance=distance
        ))

    db.create_articles_relation(items)


if __name__ == '__main__':
    total_start_time = time()
    main()

    print('FINISH Total Time, min:', (time() - total_start_time) / 60)
