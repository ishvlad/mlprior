from .models import ArticleUser


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


# def is_blogpost_like(blogpost_id, user):
#     if not user.is_authenticated:
#         return False
#
#     is_exists = BlogPostUser.objects.filter(blog_post_id=blogpost_id, user=user).count()
#
#     if not is_exists:
#         return False
#
#     blogpost_user = BlogPostUser.objects.get(blog_post_id=blogpost_id, user=user)
#
#     return blogpost_user.is_like
#
#
# def is_github_like(github_id, user):
#     if not user.is_authenticated:
#         return False
#
#     is_exists = GithubRepoUser.objects.filter(github_repo_id=github_id, user=user).count()
#
#     if not is_exists:
#         return False
#
#     github_user = GithubRepoUser.objects.get(github_repo_id=github_id, user=user)
#
#     return github_user.is_like
