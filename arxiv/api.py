import feedparser
import requests
import time


class ArXivAPI(object):
    BASE_URL = 'http://export.arxiv.org/api/query?'
    PARAMS_TEMPLATE = 'search_query={categories}&start={start}&max_results={max_result}'

    def __init__(self, wait_time=5):
        self.wait_time = wait_time
        self.time = time.time()
        pass

    def search(self, categories, start, max_result):
        # wait
        if time.time() - self.time < self.wait_time:
            time.sleep(self.wait_time - time.time() + self.time)


        categories = '+OR+'.join(categories)
        params = self.PARAMS_TEMPLATE.format(categories=categories, start=start, max_result=max_result)
        query = self.BASE_URL + params

        r = requests.get(query)
        res = feedparser.parse(r.text)

        self.time = time.time()
        return res.entries
