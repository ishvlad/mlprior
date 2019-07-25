
from articles.tasks import update_github_info, update_blog_post_info, update_reddit_info, update_website_info, update_slides_info, update_youtube_info


def github_post_save(sender, instance, signal, *args, **kwargs):
    if not kwargs['created']:
        return
    update_github_info.delay(instance.pk, first_update=True)


def blogpost_post_save(sender, instance, signal, *args, **kwargs):
    if not kwargs['created']:
        return
    update_blog_post_info.delay(instance.pk)


def reddit_post_save(sender, instance, signal, *args, **kwargs):
    if not kwargs['created']:
        return
    update_reddit_info.delay(instance.pk)


def website_post_save(sender, instance, signal, *args, **kwargs):
    if not kwargs['created']:
        return
    update_website_info.delay(instance.pk)


def slides_post_save(sender, instance, signal, *args, **kwargs):
    if not kwargs['created']:
        return
    update_slides_info.delay(instance.pk)


def youtube_post_save(sender, instance, signal, *args, **kwargs):
    if not kwargs['created']:
        return
    update_youtube_info.delay(instance.pk)
