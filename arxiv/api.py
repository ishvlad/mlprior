import requests
import feedparser


class ArXivAPI(object):
    BASE_URL = 'http://export.arxiv.org/api/query?'
    PARAMS_TEMPLATE = 'search_query={categories}&start={start}&max_results={max_result}'

    def __init__(self):
        pass

    def search(self, categories, start, max_result):
        categories = '+OR+'.join(categories)
        params = self.PARAMS_TEMPLATE.format(categories=categories, start=start, max_result=max_result)
        query = self.BASE_URL + params

        r = requests.get(query)
        res = feedparser.parse(r.text)
        return res.entries
