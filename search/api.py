

from rest_framework import permissions
from rest_framework import viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from articles.serializers import ArticlesShortSerializer
from search.documents import ArticleDocument


class SearchAPI(viewsets.GenericViewSet):
    serializer_class = ArticlesShortSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly
    ]

    def get_queryset(self):
        q = self.request.GET.get('q')
        # print('Query', q)
        articles = ArticleDocument.search().query('multi_match', query=q, fields=['title', 'abstract'])
        # print('articles', articles, articles.count())
        queryset = articles[:200].to_queryset()
        return queryset

    def list(self, request):
        queryset = self.get_queryset()

        print(queryset)

        page = request.query_params.get('page')
        if page is not None:
            paginate_queryset = self.paginate_queryset(queryset)
            serializer = self.serializer_class(paginate_queryset, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
