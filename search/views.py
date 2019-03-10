from articles.views import ArticlesView
from search.documents import ArticleDocument


class ArticlesSearchView(ArticlesView):
    def get_queryset(self):
        q = self.request.GET.get('q')
        articles = ArticleDocument.search().query('match', title=q)
        return articles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['page_name'] = 'Search for "%s"' % self.request.GET.get('q')

        return context
