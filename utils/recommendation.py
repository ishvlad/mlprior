import numpy as np
import os
import pandas as pd
import pickle
import tqdm

from articles.models import ArticleVector, Article
from django.db.models import Q
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


class RelationModel:
    def __init__(self, model_path='data/models/relations.pkl'):
        self.models_path = model_path
        if os.path.exists(self.models_path):
            title, abstract, standart_scaler = pickle.load(open(self.models_path, 'rb+'))
            self.title = title
            self.abstract = abstract
            self.standart_scaler = standart_scaler
            self.trained = True
        else:
            self.trained = False

    def get_features(self, titles, abstracts):
        features = [
            self.title.transform(titles).toarray(),
            self.abstract.transform(abstracts).toarray()
        ]
        features = self.standart_scaler.transform(np.hstack(features))

        return features

    def get_knn_dist(self, ids, features, n_neighbors=21):
        db = ArticleVector.objects.values_list('article_origin_id', 'inner_vector')
        db_features = [x[1] for x in tqdm.tqdm(db)]

        all_ids = np.array([int(x[0]) for x in db] + list(ids))

        # Find NN on full range (including new articles)
        knn = NearestNeighbors()
        knn.fit(np.concatenate((db_features, features)))

        # Who have to be updated?
        dists, nn = knn.kneighbors(db_features, n_neighbors)
        update = []
        for i in tqdm.tqdm(range(len(dists))):
            nn_ids = all_ids[nn[i][1:]]
            if np.any(np.in1d(nn_ids, ids)):
                update.append([(all_ids[i], nn_ids[j], dists[i, j]) for j in range(len(nn_ids))])

        # Add relation for new articles
        dists, nn = knn.kneighbors(features, n_neighbors)
        new = []
        for i in tqdm.tqdm(range(len(dists))):
            nn_ids = all_ids[nn[i][1:]]
            new.extend([(ids[i], nn_ids[j], dists[i, j]) for j in range(len(nn_ids))])

        return new, update

    def _convert_bytes(self, num):
        """
        this function will convert bytes to MB.... GB... etc
        """
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return "%3.1f %s" % (num, x)
            num /= 1024.0

    def retrain(self, logger, train_size=1000):
        articles = Article.objects.filter(has_txt=True)

        max_articles = articles.count()
        if train_size <= 0 or train_size >= max_articles:
            train_size = max_articles

        logger.info('Take %d articles' % train_size)
        articles = articles.order_by('date').values('title', 'abstract')[:train_size]
        articles = pd.DataFrame(articles)

        logger.info('Training Title TD-IDF')
        model_title = TfidfVectorizer(decode_error='replace', max_features=20,
                                      ngram_range=(1, 2), stop_words='english', strip_accents='unicode')
        features_title = model_title.fit_transform(articles.abstract.values).toarray()

        logger.info('Training Abstract TD-IDF')
        model_abstract = TfidfVectorizer(decode_error='replace', max_features=50,
                                         ngram_range=(1, 2), stop_words='english', strip_accents='unicode')
        features_abstract = model_abstract.fit_transform(articles.abstract.values).toarray()

        logger.info('Training Standart Scaler')
        features = np.hstack([
            features_title,
            features_abstract
        ])
        ss = StandardScaler().fit(features)

        logger.info('Saving models')
        pickle.dump((model_title, model_abstract, ss), open(self.models_path, 'wb+'))
        logger.info('Models saved. Total size = %s' % self._convert_bytes(os.path.getsize(self.models_path)))
