import os
import sys
from time import sleep, time

sys.path.append('./')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import django

django.setup()

from articles.models import Article as ArticleModel, Author
from arxiv import ArXivArticle, ArXivAPI


class DBManager(object):
    def __init__(self):
        pass

    def add_author(self, name, article):
        pass

    def add_article(self, arxiv_article):
        article, _ = ArticleModel.objects.update_or_create(
            arxiv_id=arxiv_article.id,
            version=arxiv_article.version,
            title=arxiv_article.title,
            abstract=arxiv_article.abstract,
            url=arxiv_article.pdf_url,
            date=arxiv_article.date,
            category=arxiv_article.category
        )

        article.save()

        # authors = []

        for name in arxiv_article.authors:
            author, created = Author.objects.get_or_create(name=name)
            author.save()
            # authors.append(author)

            article.authors.add(author)


def main():
    arxiv_api = ArXivAPI()

    for start in range(0, 100, 100):
        print(start)
        entries = arxiv_api.search(categories=[
            'cat:cs.CV',
            'cat:cs.AI',
            'cat:cs.LG',
            'cat:cs.CL',
            'cat:cs.NE',
            'cat:cs.ML',
        ], start=start, max_result=100)

        db = DBManager()

        for record in entries:
            arxiv_article = ArXivArticle(record)
            db.add_article(arxiv_article)

        sleep(5.)


if __name__ == '__main__':
    total_start_time = time()
    main()

    print('Total Time, min:', (time() - total_start_time) / 60)
