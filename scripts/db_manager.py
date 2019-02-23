from articles.models import Article as ArticleModel, Author, ArticleText, ArticleVector, ArticleArticleRelation


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

        return article.id

    def add_article_text(self, article_id, pdf_location, txt_location, text):
        article, _ = ArticleText.objects.update_or_create(
            article_origin_id=article_id,
            pdf_location=pdf_location,
            txt_location=txt_location,
            text=text
        )

        article.save()

    def bulk_create(self, base_class, items):
        base_class.objects.bulk_create(items)

    def create_articles_vectors(self, items):
        ArticleVector.objects.bulk_create(items)

    def create_articles_relation(self, items):
        ArticleArticleRelation.objects.bulk_create(items)

    def article_filter_by_existance(self, arxiv_ids):
        articles = ArticleModel.objects.filter(arxiv_id__in=arxiv_ids).values_list('arxiv_id', flat=True)

        return [idx not in articles for idx in arxiv_ids]
