from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from el_pagination.decorators import page_template

from articles.documents import ArticleDocument
from articles.forms import UserForm
from articles.models import Article, User, Author


@login_required(login_url='/login')
def home(request):
    n_articles = Article.objects.count()

    n_articles_in_lib = request.user.articles.count()

    context = {
        'n_articles': n_articles,
        'n_articles_in_lib': n_articles_in_lib

    }

    return render(request, 'home.html', context)

@page_template('articles_list_page.html')
@login_required(login_url='/login')
def articles(request, template='articles_list.html', extra_context=None):
    all_articles = Article.objects.order_by('-date')

    user_articles = request.user.articles.all()

    context = {
        'articles': all_articles,
        'user_articles': user_articles,
        'page_name': 'Articles',
        'is_lib': False
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


@page_template('related_articles_page.html')
@login_required(login_url='/login')
def article_details(request, article_id, template='article_details.html', extra_context=None):
    article = get_object_or_404(Article, id=article_id)

    related_articles = Article.objects.order_by('-date')
    user_articles = request.user.articles.all()

    context = {
        'article': article,
        'related_articles': related_articles,
        'user_articles': user_articles
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


@page_template('articles_list_page.html')
@login_required(login_url='/login')
def author_articles(request, author_name, template='articles_list.html', extra_context=None):
    # all_articles = Article.objects.order_by('-date')

    user = Author.objects.get(name=author_name)
    user_articles = request.user.articles.all()

    context = {
        'articles': user.articles.all(),
        'page_name': 'Articles of %s' % user.name,
        'user_articles': user_articles,
        'is_lib': False
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


@login_required(login_url='/login')
def add_remove_from_library(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if request.method == 'POST':
        article.users.add(request.user)
        data = {
            'is_ok': 'ok!'
        }
    elif request.method == 'DELETE':
        article.users.remove(request.user)
        data = {
            'is_ok': 'deleted!'
        }
    else:
        data = {}

    return JsonResponse(data)


@login_required(login_url='/login')
def change_note(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    print('Current notes', article.note)

    if request.method == 'POST':
        print(request.POST.get('note', ''))
        article.note = request.POST.get('note', '')
        article.save()

    data = {
        'is_ok': 'deleted!'
    }

    return JsonResponse(data)


@page_template('articles_list_page.html')
@login_required(login_url='/login')
def search(request, search_query, template='articles_list.html', extra_context=None):
    print('SEARCH!!!')
    s = ArticleDocument.search().query("match", title=search_query)

    for art in s:
        print(art)

    user_articles = request.user.articles.all()

    context = {
        'articles': s.to_queryset(),
        'user_articles': user_articles,
        'page_name': 'Articles',
        'is_lib': False
    }

    if extra_context is not None:
        context.update(extra_context)

    rendered_template = render(request, template, context)
    return HttpResponse(rendered_template, content_type='text/html')


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
