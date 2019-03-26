from articles.models import Article
from articles.views import ArticlesView
from search.documents import ArticleDocument
from dal import autocomplete


class ArticlesSearchView(ArticlesView):
    def get_queryset(self):
        q = self.request.GET.get('q')
        articles = ArticleDocument.search().query('multi_match', query=q, fields=['title', 'abstract'])
        articles = articles.to_queryset()
        return articles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['page_name'] = 'Search for "%s"' % self.request.GET.get('q')

        return context


class ArticlesAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        # if not self.request.user.is_authenticated():
        #     return Article.objects.none()

        qs = Article.objects.all()

        if self.q:
            qs = qs.filter(title__istartswith=self.q)

        return qs