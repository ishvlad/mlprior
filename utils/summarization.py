# import nltk
# nltk.download('punkt')

import numpy as np
from nltk import tokenize
from gensim.summarization import summarize


class SummarizationModel:
    def __init__(self):
        self.num_sentences = 5
        self.min_sentence_length = 20

    @staticmethod
    def _preprocess(txt):
        # replace empty lines with EOS
        txt = txt.replace('\n \n', '.')

        # replace line break with whitespace
        txt = txt.replace('\n', ' ')

        return txt

    def summarize(self, txt):
        text = self._preprocess(txt)

        # text to sentences list
        sentences = tokenize.sent_tokenize(text)

        # delete short sentences
        lens = np.array([len(x) for x in sentences])
        sentences = np.array(sentences)[lens > self.min_sentence_length]

        importance = {}
        n = 1
        # this loop need only for importance
        while True:
            summary = summarize('\n'.join(sentences), ratio=n/len(sentences), split=True)

            # less importance for bigger summary (only for new sentences)
            for i, s in enumerate(summary):
                if s not in importance:
                    importance[s] = [n-1]

            # if done, append chronology
            if len(summary) >= self.num_sentences:
                for i, s in enumerate(summary):
                    importance[s].append(i)

                break
            n += 1

        # tuples (sentence, importance, chronology)
        result = [(k, v[0], v[1]) for k, v in importance.items()]
        return result
