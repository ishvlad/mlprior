import feedparser
import requests
import time


class ArXivAPI(object):
    BASE_URL = 'http://export.arxiv.org/api/query?'
    PARAMS_TEMPLATE = 'search_query={categories}&start={start}&max_results={max_result}'
    SORT_TEMPLATE = '&sortBy=lastUpdatedDate'

    def __init__(self, wait_time=5,  categories=[]):
        self.wait_time = wait_time
        self.time = time.time()

        self.categories = '+OR+'.join(categories)
        assert len(self.categories) > 0

    def search(self, start, max_result, is_random=False):
        # wait
        if time.time() - self.time < self.wait_time:
            time.sleep(self.wait_time - time.time() + self.time)

        params = self.PARAMS_TEMPLATE.format(categories=self.categories, start=start, max_result=max_result)
        query = self.BASE_URL + params
        if not is_random:
            query += self.SORT_TEMPLATE

        r = requests.get(query)
        res = feedparser.parse(r.text)

        self.time = time.time()
        return res.entries
