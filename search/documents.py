from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.documents import Document
from django_elasticsearch_dsl.registries import registry

from articles.models import Article, Author


@registry.register_document
class ArticleDocument(Document):
    authors = fields.NestedField(properties={
        'name': fields.TextField(),
    })

    class Index:
        # Name of the Elasticsearch index
        name = 'articles'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = Article

        fields = [
            'title',
            'arxiv_id',
            'abstract',
            'url',
            'date',
            'category'
        ]

        related_models = [Author]

    def get_instances_from_related(self, related_instance):
        """If related_models is set, define how to retrieve the Car instance(s) from the related model.
        The related_models option should be used with caution because it can lead in the index
        to the updating of a lot of items.
        """
        if isinstance(related_instance, Author):
            return related_instance.articles
