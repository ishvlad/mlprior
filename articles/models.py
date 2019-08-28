from django.conf import settings
from django.contrib.postgres.fields import HStoreField
from django.db import models
from taggit.managers import TaggableManager

from core.search import ArticleIndex
from model_utils.managers import InheritanceManager

User = settings.AUTH_USER_MODEL


class Article(models.Model):
    arxiv_id = models.CharField(max_length=50)
    version = models.CharField(max_length=10, verbose_name='Version')

    title = models.CharField(max_length=1000, verbose_name='Title')
    abstract = models.TextField(verbose_name='Abstract')
    url = models.URLField(verbose_name='URL')
    date = models.DateField()
    category = models.CharField(max_length=100)

    users = models.ManyToManyField(User, 'articles', through='ArticleUser')

    has_pdf = models.NullBooleanField(default=False)
    has_txt = models.NullBooleanField(default=False)
    has_inner_vector = models.BooleanField(default=False)
    has_summary = models.BooleanField(default=False)
    has_sitemap = models.BooleanField(default=False)
    has_neighbors = models.BooleanField(default=False)
    has_category_bar = models.BooleanField(default=False)
    has_ngram_stat = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['date']

    def __str__(self):
        return self.title

    def indexing(self):
        obj = ArticleIndex(
            meta={'id': self.id},
            title=self.title
        )
        obj.save()
        return obj.to_dict(include_meta=True)


class Author(models.Model):
    name = models.CharField(max_length=100, verbose_name='Author name', primary_key=True)

    articles = models.ManyToManyField(Article, 'authors')

    has_sitemap = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'
        ordering = ['name']

    def __str__(self):
        return self.name


class Resource(models.Model):
    url = models.URLField(verbose_name='URL')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='resources')
    users = models.ManyToManyField(User, related_name='resources', through='ResourceUser')
    who_added = models.ForeignKey(User, related_name='added_resource', on_delete=models.CASCADE, default=1)
    rating = models.PositiveIntegerField(verbose_name='rating', default=0)

    objects = InheritanceManager()  # in order to use select_subclasses() method

    def __str__(self):
        return '%s | %s' % (self.article.title, self.url)


class BlogPost(Resource):
    title = models.CharField(verbose_name='title', max_length=300, default=None, null=True)
    description = models.TextField(verbose_name='description', default=None, null=True)
    image = models.URLField(verbose_name='image_url', default=None, null=True)

    @property
    def type(self):
        return 'blogpost'


class GitHub(Resource):
    title = models.CharField(verbose_name='title', max_length=300, null=True)
    description = models.TextField(verbose_name='description', default='', null=True)

    topics = TaggableManager()
    n_stars = models.PositiveIntegerField(verbose_name='stars', default=0, null=True)
    language = models.CharField(verbose_name='language', max_length=100, default='', null=True)
    framework = models.CharField(verbose_name='framework', max_length=100, default='', null=True)
    languages = HStoreField(default=dict, blank=True)
    is_official = models.BooleanField(verbose_name='is_official', default=False, null=True)

    @property
    def type(self):
        return 'github'


class YouTube(Resource):
    title = models.CharField(verbose_name='title', max_length=300, default=None, null=True)
    description = models.TextField(verbose_name='description', default=None, null=True)
    image = models.URLField(verbose_name='image_url', default=None, null=True)

    @property
    def type(self):
        return 'youtube'


class WebSite(Resource):
    title = models.CharField(verbose_name='title', max_length=300, default=None, null=True)
    description = models.TextField(verbose_name='description', default=None, null=True)
    image = models.URLField(verbose_name='image_url', default=None, null=True)

    @property
    def type(self):
        return 'website'


class Slides(Resource):
    title = models.CharField(verbose_name='title', max_length=300, default=None, null=True)
    description = models.TextField(verbose_name='description', default=None, null=True)
    image = models.URLField(verbose_name='image_url', default=None, null=True)

    @property
    def type(self):
        return 'slides'


class Reddit(Resource):
    title = models.CharField(verbose_name='title', max_length=300, default=None, null=True)
    description = models.TextField(verbose_name='description', default=None, null=True)
    image = models.URLField(verbose_name='image_url', default=None, null=True)

    @property
    def type(self):
        return 'reddit'


class ResourceUser(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    is_like = models.BooleanField(verbose_name='like', default=False)

    class Meta:
        unique_together = (('resource', 'user'),)


class ArticleUser(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='article_user')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='article_user')

    note = models.TextField(verbose_name='Note', default='')
    like_dislike = models.NullBooleanField()
    in_lib = models.BooleanField(default=False)

    def __str__(self):
        return '%s | %s' % (self.user.email, self.article.title)

    class Meta:
        unique_together = (('article', 'user'),)


class UserTags(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    tags = HStoreField(default=dict)
    n_articles = models.IntegerField(default=0)


class ArticleText(models.Model):
    article_origin = models.OneToOneField(
        Article,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    pdf_location = models.CharField(max_length=100)
    txt_location = models.CharField(max_length=100)

    text = models.CharField(max_length=100000)
    tags = HStoreField(default=dict)  # key -- tag, value -- freq (BoW)
    tags_norm = models.IntegerField(default=0)

    relations = HStoreField(default=dict)  # key -- article pk, value -- distance


class ArticleSentence(models.Model):
    article_origin = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='summary_sentences')

    sentence = models.CharField(max_length=10000)
    n_likes = models.PositiveIntegerField(default=0)
    n_dislikes = models.PositiveIntegerField(default=0)
    chronology = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Summary Sentence'
        verbose_name_plural = 'Summary Sentences'

    def __str__(self):
        return '%s | %s' % (self.chronology, self.article_origin.title)


class NGramsMonth(models.Model):
    label = models.CharField(max_length=6)  # bbb YY
    label_code = models.IntegerField()  # YYYYMM
    type = models.IntegerField()  # 0 - title, 1 - abstract, 2 - text

    sentences = HStoreField(default=dict)  # key -- sentence, value -- frequency (as string)

    class Meta:
        unique_together = (('type', 'label_code'),)


class Categories(models.Model):
    category = models.CharField(max_length=50, primary_key=True)
    category_full = models.CharField(max_length=1000)

    months = HStoreField(default=dict)


# class Authorship(models.Model):
#     author = models.ForeignKey(Author, on_delete=models.CASCADE)
#     article = models.ForeignKey(Article, on_delete=models.CASCADE)

#


class DefaultStore(models.Model):
    key = models.CharField(primary_key=True, max_length=1000)
    value = models.CharField(default='', max_length=500000)



