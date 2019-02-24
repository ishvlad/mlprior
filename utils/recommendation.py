import numpy as np
import pickle
import tqdm

from articles.models import ArticleVector
from sklearn.neighbors import NearestNeighbors


class RelationModel:
    def __init__(self):
        title, abstract, text, standart_scaler = pickle.load(open('data/models/relations.pkl', 'rb+'))
        self.title = title
        self.abstract = abstract
        self.text = text
        self.standart_scaler = standart_scaler

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
