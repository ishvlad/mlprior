

class ArXivArticle(object):
    def __init__(self, entry):
        self.entry = entry

    def get_id_version(self, url):
        # http://arxiv.org/abs/1512.08756v2
        id_version = url.split('/')[-1]
        parts = id_version.split('v')
        return parts[0], parts[1]

    @property
    def id(self):
        return self.get_id_version(self.entry['id'])[0]

    @property
    def version(self):
        return self.get_id_version(self.entry['id'])[1]

    @property
    def authors(self):
        return [name['name'] for name in self.entry['authors']]

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

    @property
    def date(self):
        return self.entry['published'].split('T')[0]

    @property
    def category(self):
        return self.entry['arxiv_primary_category']['term']
