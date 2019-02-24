from django.contrib.auth.models import User
from django.db import models


class Article(models.Model):
    arxiv_id = models.CharField(max_length=50)
    version = models.CharField(max_length=10, verbose_name='Version')

    title = models.CharField(max_length=1000, verbose_name='Title')
    abstract = models.TextField(verbose_name='Abstract')
    url = models.URLField(verbose_name='URL')
    date = models.DateField()
    category = models.CharField(max_length=100)

    users = models.ManyToManyField(User, 'articles', through='ArticleUser')
    related = models.ManyToManyField('self', 'related_articles', through='ArticleArticleRelation',
                                     symmetrical=False)

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['date']

    def __str__(self):
        return self.title


class Author(models.Model):
    name = models.CharField(max_length=100, verbose_name='Author name', primary_key=True)

    articles = models.ManyToManyField(Article, 'authors')

    class Meta:
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'
        ordering = ['name']

    def __str__(self):
        return self.name


class ArticleUser(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    note = models.TextField(verbose_name='Note', default='')
    like_dislike = models.NullBooleanField()
    in_lib = models.BooleanField(default=False)

    class Meta:
        unique_together = (('article', 'user'),)


class ArticleArticleRelation(models.Model):
    left = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='from_article')
    right = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='to_article')

    distance = models.FloatField()


class ArticleText(models.Model):
    article_origin = models.OneToOneField(
        Article,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    text = models.CharField(max_length=100000)

    pdf_location = models.CharField(max_length=100)
    txt_location = models.CharField(max_length=100)


class ArticleVector(models.Model):
    article_origin = models.OneToOneField(
        Article,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    inner_vector = models.BinaryField(max_length=100000)


class NGramsMonth(models.Model):
    length = models.IntegerField()
    label = models.CharField(max_length=6)
    label_code = models.IntegerField()

    related = models.ManyToManyField('NGramsSentence', through='SentenceVSMonth')

    class Meta:
        unique_together = (('length', 'label_code'),)


class NGramsSentence(models.Model):
    sentence = models.CharField(max_length=250, primary_key=True)

    corpora = models.ManyToManyField(NGramsMonth, through='SentenceVSMonth')


class SentenceVSMonth(models.Model):
    from_corpora = models.ForeignKey(NGramsMonth, on_delete=models.CASCADE)
    from_item = models.ForeignKey(NGramsSentence, on_delete=models.CASCADE)

    freq_title = models.IntegerField(default=0)
    freq_abstract = models.IntegerField(default=0)
    freq_text = models.IntegerField(default=0)

    class Meta:
        unique_together = (('from_corpora', 'from_item'),)


class Categories(models.Model):
    category = models.CharField(max_length=10, primary_key=True)
    category_full = models.CharField(max_length=1000)

    month = models.ManyToManyField('CategoriesDate', through='CategoriesVSDate')


class CategoriesDate(models.Model):
    date_code = models.IntegerField(primary_key=True)
    date = models.CharField(max_length=6)

    category = models.ManyToManyField('Categories', through='CategoriesVSDate')


class CategoriesVSDate(models.Model):
    from_category = models.ForeignKey(Categories, on_delete=models.CASCADE)
    from_month = models.ForeignKey(CategoriesDate, on_delete=models.CASCADE)

    count = models.IntegerField()

    class Meta:
        unique_together = (('from_category', 'from_month'),)



# class Authorship(models.Model):
#     author = models.ForeignKey(Author, on_delete=models.CASCADE)
#     article = models.ForeignKey(Article, on_delete=models.CASCADE)

#
