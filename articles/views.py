from django.shortcuts import render, get_object_or_404

from articles.forms import UserForm
from articles.models import Article
from django.contrib.auth.decorators import login_required


def articles(request):
    all_articles = Article.objects.all()
    return render(request, 'articles.html', {'articles': all_articles})


@login_required(login_url='/login')
def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    return render(request, 'article_detail.html', {'article': article})


def sign_up(request):
    user_form = UserForm()
    return render(request, 'sign_up.html', {
        'user_form': user_form
    })
