from django.shortcuts import render, get_object_or_404

from articles.forms import UserForm
from articles.models import Article, Author
from django.contrib.auth.decorators import login_required
from el_pagination.decorators import page_template


@page_template('articles_list_page.html')
def articles(request, template='articles_list.html', extra_context=None):
    all_articles = Article.objects.order_by('-date')

    context = {
        'articles': all_articles,
    }

    if extra_context is not None:
        context.update(extra_context)

    return render(request, template, context)


@login_required(login_url='/login')
def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    return render(request, 'article_detail.html', {'article': article})


def sign_up(request):
    user_form = UserForm()
    return render(request, 'sign_up.html', {
        'user_form': user_form
    })
