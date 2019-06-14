from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl import DocType, Text, Search
from elasticsearch_dsl.connections import connections

from articles import models as articles_models

connections.create_connection()


class ArticleIndex(DocType):
    title = Text()

    class Meta:
        index = 'article-index'


def bulk_indexing():
    ArticleIndex.init()
    es = Elasticsearch()
    bulk(client=es, actions=(b.indexing() for b in articles_models.Article.objects.all().iterator()))


def search(title):
    s = Search().filter('term', title=title)
    response = s.execute()
    return response
