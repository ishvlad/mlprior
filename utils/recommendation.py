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
    def __init__(self):
        models_path = 'data/models/relations.pkl'
        if os.path.exists(models_path):
            title, abstract, text, standart_scaler = pickle.load(open(models_path, 'rb+'))
            self.title = title
            self.abstract = abstract
            self.text = text
            self.standart_scaler = standart_scaler
            self.trained = True
        else:
            self.trained = False

    def get_features(self, titles, abstracts, texts):
        features = [
            self.title.transform(titles).toarray(),
            self.abstract.transform(abstracts).toarray(),
            self.text.transform(texts).toarray()
        ]
        features = self.standart_scaler.transform(np.hstack(features))

        return features

    def get_knn_dist(self, ids, features, n_neighbors=21):
        db = ArticleVector.objects.values_list('article_origin_id', 'inner_vector')
        db_features = [np.frombuffer(x[1]) for x in tqdm.tqdm(db)]

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

    def retrain(self, train_size=1000):
        articles = Article.objects.filter(has_txt=True)

        max_articles = articles.count()
        if train_size <= 0 or train_size >= max_articles:
            train_size = max_articles

        articles = articles.order_by('date').values('title', 'abstract', 'articletext__text')[:train_size]
        articles = pd.DataFrame(articles)

        model_title = TfidfVectorizer(decode_error='replace', max_features=20,
                                      ngram_range=(1, 2), stop_words='english', strip_accents='unicode')
        features_title = model_title.fit_transform(articles.abstract.values).toarray()

        model_abstract = TfidfVectorizer(decode_error='replace', max_features=50,
                                         ngram_range=(1, 2), stop_words='english', strip_accents='unicode')
        features_abstract = model_abstract.fit_transform(articles.abstract.values).toarray()

        model_text = TfidfVectorizer(decode_error='replace', max_features=230,
                                     ngram_range=(1, 2), stop_words='english', strip_accents='unicode')
        features_text = model_text.fit_transform(articles.articletext__text.values).toarray()

        features = np.hstack([
            features_title,
            features_abstract,
            features_text
        ])
        ss = StandardScaler().fit_transform(features)

        pickle.dump((model_title, model_abstract, model_text, ss), open('data/models/relations.pkl', 'wb+'))

