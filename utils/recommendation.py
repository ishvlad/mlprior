import nltk
import numpy as np
import os
import re
import spacy
import string

from articles.models import UserTags
from collections import Counter



class RelationModel:
    def __init__(self, bigram_path='data/models/bigram_model.pkl'):
        self.model_path = bigram_path
        if os.path.exists(self.model_path):
            nltk.download('stopwords')
            from nltk.corpus import stopwords
            from gensim.utils import simple_preprocess
            from gensim.models.phrases import Phraser

            self.preprocess = simple_preprocess
            self.bigram_model = Phraser.load(bigram_path)

            self.stop_words = stopwords.words('english')
            self.stop_words.extend([
                'arxiv', 'com',
                'leq', 'geq', 'cdot', 'frac'
            ])

            self.nlp = spacy.load('en', disable=['parser', 'ner'])
            self.trained = True
        else:
            self.trained = False

    def _sent_to_words(self, sentence):
        important_words = ['3d', '2d', '1d']
        replace = [''.join(np.random.choice(list(string.ascii_lowercase), 10)) for _ in important_words]

        # encode important numbers
        new_sentence = sentence
        for iw, r in zip(important_words, replace):
            new_sentence = new_sentence.replace(iw, r)

        # delete bad text
        words = self.preprocess(new_sentence, deacc=True, max_len=30)
        words = [re.sub('[^A-Za-z )]', '', w) for w in words]

        # delete stopwords
        new_sentence = ' '.join([w for w in words if w not in self.stop_words])
        # decode important numbers
        for iw, r in zip(important_words, replace):
            new_sentence = new_sentence.replace(r, iw)

        return new_sentence.split()

    def get_tags(self, title, abstract, text):
        text = ' '.join([title, abstract, text])
        text = self._sent_to_words(text)

        # words -> words or bigrams
        text = self.bigram_model[text]

        # Lemmatization
        allowed_postags = ['ADJ', 'ADV', 'NOUN', 'NUM']
        text = self.nlp(" ".join(text))
        text = [token.lemma_ for token in text if token.pos_ in allowed_postags]

        # Get most frequent
        tags = dict(Counter(text).most_common(100))
        return tags

    @staticmethod
    def get_dist(source_tags, target_tags, source_norm, target_norm):
        result_mae = 0

        for key in source_tags:
            if key in target_tags:
                a = float(source_tags[key]) / float(source_norm)
                b = float(target_tags[key]) / float(target_norm)
                result_mae += max(a - b, b - a)
            else:
                result_mae += float(source_tags[key]) / float(source_norm)

        remain = sum([float(target_tags[key]) for key in target_tags if key not in source_tags])
        result_mae += remain / float(target_norm)
        return result_mae

    @staticmethod
    def add_user_tags(user_tags, user_n_articles, article_tags, article_tags_norm):
        article_tags = article_tags.copy()
        for k in article_tags:
            article_tags[k] = float(article_tags[k]) / article_tags_norm

        if len(user_tags) == 0:
            return article_tags

        learning_rate = 1. / min(20, user_n_articles + 1)
        result = {}
        for k in user_tags:
            result[k] = (1-learning_rate) * float(user_tags[k])
        for k in article_tags:
            if k in result:
                result[k] += learning_rate * float(article_tags[k])
            else:
                result[k] = learning_rate * float(article_tags[k])

        items = sorted(result.items(), key=lambda x: x[1], reverse=True)
        result = dict(items[:500])

        norm = sum(result.values())
        for k in result:
            result[k] /= norm

        return result
