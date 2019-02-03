from django.shortcuts import render, get_object_or_404

from articles.forms import UserForm
from articles.models import Article, Author, User
from django.contrib.auth.decorators import login_required
from el_pagination.decorators import page_template
from django.http import JsonResponse


@page_template('articles_list_page.html')
@login_required(login_url='/login')
def articles(request, template='articles_list.html', extra_context=None):
    all_articles = Article.objects.order_by('-date')

    # print(request.method)

    # if request.method == 'POST':
    #     print(request.body)

    context = {
        'articles': all_articles,
        'page_name': 'Articles',
        'user': request.user,
        'is_lib': False
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


def like(request):
    print('LIKE')
    print(request.method, request.body, request.user)

    if request.method == 'GET':
        Article.objects.get(id=request.GET.get('article_id')).users.add(request.user)
        data = {
            'is_ok': 'ok!'
        }
    elif request.method == 'DELETE':
        Article.objects.get(id=request.GET.get('article_id')).users.remove(request.user)
        data = {
            'is_ok': 'deleted!'
        }
    else:
        data = {}

    return JsonResponse(data)


@page_template('articles_list_page.html')
@login_required(login_url='/login')
def library(request, template='articles_list.html', extra_context=None):

    all_articles = request.user.articles.all()

    context = {
        'articles': all_articles,
        'page_name': 'Library',
        'is_lib': True
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


def register(request):
    user_form = UserForm()
    return render(request, 'register.html', {
        'user_form': user_form
    })
