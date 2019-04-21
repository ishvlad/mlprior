from django_elasticsearch_dsl import DocType, Index

from articles.models import Article

articles = Index('articles')
articles.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@articles.doc_type
class ArticleDocument(DocType):
    class Meta:
        model = Article

        fields = [
            'title',
            'arxiv_id',
            'abstract',
            'url',
            'date',
            'category'
        ]