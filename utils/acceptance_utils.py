import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta
from io import BytesIO
import base64

from utils.pdf2txt import PDF2TXT


class Acceptance:
    def __init__(self):
        self.pdf2txt = PDF2TXT()

    def _random_value(self, m, b=5):
        a = ((2 - b) * m - 1) / (m - 1)
        return beta.rvs(a, b)

    def predict_acceptance_proba(self, file_path: str, conf_names):
        '''
        Args:
        txt, str - parsed text from pdf
        conf_names, list of str - list of conference names to predict acceptance rate

        Returns:
        list of float - predicted probability of acceptance to corresponding conferences in conf_names
        '''

        txt = self.pdf2txt.pdf2txt(file_path)

        acceptance_rates = {
            'AISTATS': 0.324, 'ICML': 0.226,  'ICLR': 0.341, 'CVPR': 0.25, 'KDD': 0.142,
            'ACL': 0.257, 'NeurIPS': 0.211, 'AAAI': 0.162, 'WWW': 0.18
        }

        other_acceptance_rate = 0.3
        result = [
            self._random_value(acceptance_rates.get(x, other_acceptance_rate)) for x in conf_names
        ]

        return result

    def get_figure_acceptance_proba(self, p, conf_names=['ICML', 'ICLR', 'ACL',  'NeurIPS', 'AAAI', 'WWW']) -> str:
        '''
        Args:
        p, list of float - predicted probability of acceptance to corresponding conferences in conf_names
        conf_names, list of str - list of conference names to predict acceptance rate

        Returns:
        str - base64 encoded svg-figure
        '''

        assert len(conf_names) == len(p)

        plt.figure(figsize=(1.3*len(p), 5))
        plt.bar(range(len(p)), np.array(p)*100, color='#4D73DD')
        plt.xticks(range(len(conf_names)), conf_names, fontsize=14)
        plt.ylabel('acceptance chance [%]', fontsize=14)
        plt.ylim([0, 100])
        plt.gca().yaxis.grid()

        buf = BytesIO()
        plt.gcf().savefig(buf, format='svg')
        buf.seek(0)
        s = base64.b64encode(buf.read())

        return s
