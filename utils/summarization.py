# import nltk
# nltk.download('punkt')

import string
import numpy as np
from nltk import tokenize
from gensim.summarization import summarize


class SummarizationModel:
    def __init__(self):
        self.num_sentences = 5
        self.min_sentence_length = 40
        self.min_percent = 0.7

    @staticmethod
    def _get_percent(sentence):
        sentence = list(sentence.replace(' ', ''))
        mask = np.in1d(sentence, list(string.ascii_letters))

        return mask.sum() / len(sentence)

    def _preprocess(self, txt):
        # replace empty lines with EOS
        txt = txt.replace('\n \n', '.')

        # replace line break with whitespace
        txt = txt.replace('\n', ' ')

        # text to sentences list
        sentences = tokenize.sent_tokenize(txt)

        # delete short sentences
        lens = np.array([len(x) for x in sentences])
        sentences = np.array(sentences)[lens > self.min_sentence_length]

        # filter out all sentences with non-char elements (utf-8)
        sentences = [s for s in sentences if sum(np.array(list(bytes(s, 'utf-8'))) > 128) == 0]

        # filter out all sentences, where proportion of letters is less than self.min_percent
        sentences = [s for s in sentences if SummarizationModel._get_percent(s) > self.min_percent]

        return sentences

    def summarize(self, txt):
        sentences = self._preprocess(txt)

        summary = summarize('\n'.join(sentences), ratio=self.num_sentences/len(sentences), split=True)

        # tuples (chronology, sentence)
        result = list(enumerate(summary))
        return result
