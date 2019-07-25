from .models import ArticleUser, ResourceUser


def is_article_in_lib(article_id, user):
    if not user.is_authenticated:
        return False

    is_exists = ArticleUser.objects.filter(article_id=article_id, user=user).count()

    if not is_exists:
        return False

    article_user = ArticleUser.objects.get(article_id=article_id, user=user)

    return article_user.in_lib


def like_dislike(article_id, user):
    if not user.is_authenticated:
        return None

    is_exists = ArticleUser.objects.filter(article_id=article_id, user=user).count()

    if not is_exists:
        return None

    article_user = ArticleUser.objects.get(article_id=article_id, user=user)

    return article_user.like_dislike


def get_note(article_id, user):
    if not user.is_authenticated:
        return ''

    is_exists = ArticleUser.objects.filter(article_id=article_id, user=user).count()

    if not is_exists:
        return ''

    article_user = ArticleUser.objects.get(article_id=article_id, user=user)

    return article_user.note


def is_resource_like(resource_id, user):
    if not user.is_authenticated:
        return False

    is_exists = ResourceUser.objects.filter(resource_id=resource_id, user=user).count()

    if not is_exists:
        return False

    resource_user = ResourceUser.objects.get(resource_id=resource_id, user=user)

    return resource_user.is_like

