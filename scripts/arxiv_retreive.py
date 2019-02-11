import argparse
import os
import sys
from time import sleep, time
import tqdm

sys.path.append('./')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import django

django.setup()

from articles.models import Article as ArticleModel, Author, ArticleArticleRelation, \
    NGramsCorporaByMonth, NGramsCorporaItem, CorporaItem
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

    def create_articles_relation(self, items):
        ArticleArticleRelation.objects.bulk_create(items)

    def create_ngram_corpora(self, items):
        NGramsCorporaByMonth.objects.bulk_create(items)

    def create_ngram_item(self, items):
        NGramsCorporaItem.objects.bulk_create(items)

    def create_corpora_item_link(self, items):
        CorporaItem.objects.bulk_create(items)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--article_per_it', type=int, help='Articles per iteration', default=100)
    parser.add_argument('--n_articles', type=int, help='number of data loading workers', default=1000)
    parser.add_argument('--sleep_time', type=int, help='How much time of sleep (in sec) between API calls', default=5)

    args = parser.parse_args()
    return args


def main(args):
    arxiv_api = ArXivAPI()

    for start in tqdm.tgrange(0, args.n_articles, args.article_per_it):
        entries = arxiv_api.search(categories=[
            'cat:cs.CV',
            'cat:cs.AI',
            'cat:cs.LG',
            'cat:cs.CL',
            'cat:cs.NE',
            'cat:cs.ML',
        ], start=start, max_result=args.article_per_it)

        db = DBManager()

        for record in entries:
            arxiv_article = ArXivArticle(record)
            db.add_article(arxiv_article)

        sleep(args.sleep_time)


if __name__ == '__main__':
    args = parse_args()
    total_start_time = time()
    main()

    print('Total Time, min:', (time() - total_start_time) / 60)
