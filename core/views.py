from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from el_pagination.decorators import page_template


# @page_template('articles_list_page.html')
# @login_required(login_url='/accounts/login')
# def search(request, search_query, template='articles_list.html', extra_context=None):
#     print('SEARCH!!!')
#     s = search.search().query("match", title=search_query)
#
#     for art in s:
#         print(art)
#
#     user_articles = request.user.articles.all()
#
#     context = {
#         'articles': s.to_queryset(),
#         'user_articles': user_articles,
#         'page_name': 'Articles',
#         'is_lib': False
#     }
#
#     if extra_context is not None:
#         context.update(extra_context)
#
#     rendered_template = render(request, template, context)
#     return HttpResponse(rendered_template, content_type='text/html')
