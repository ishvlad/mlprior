

class ArXivArticle(object):
    def __init__(self, entry):
        self.entry = entry

    @property
    def id(self):
        return self.entry['id']

    @property
    def pdf_url(self):
        for l in self.entry['links']:
            if l['type'] != 'application/pdf':
                continue
            return l['href']

        return ''

    @property
    def title(self):
        return self.entry['title']

    @property
    def abstract(self):
        return self.entry['summary']
