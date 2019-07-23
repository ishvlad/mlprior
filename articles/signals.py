# from django.db.models.signals import post_save
# from django.dispatch import receiver
#
# from articles.models import GitHubRepository
# from articles.tasks import update_github_info, update_blog_post_info
#
#
# def github_post_save(sender, instance, signal, *args, **kwargs):
#     print('HUY!')
#     print(instance.url, sender, signal)
#
#     update_github_info.delay(instance.pk)
#
#
# def blogpost_post_save(sender, instance, signal, *args, **kwargs):
#     update_blog_post_info.delay(instance.pk)
