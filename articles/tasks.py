from celery.schedules import crontab
from celery.task import periodic_task
from github import UnknownObjectException

from articles.models import GitHub, BlogPost, YouTube, Reddit, Slides, WebSite
from mlprior.celery import app
from services.github.repository import GitHubRepo
from webpreview import web_preview


@app.task(max_retries=10, name='mlprior.articles.tasks.update_github_info', rate_limit='100/h')
def update_github_info(github_id, first_update=True):
    print('Updating GitHub with id=%s' % github_id)
    repo = GitHub.objects.get(id=github_id)

    url = repo.url

    try:
        g = GitHubRepo(url)
    except UnknownObjectException as e:
        print("The repository doesn't exist")
        return

    repo.title = g.name
    repo.n_stars = g.n_stars
    repo.description = g.description

    if first_update:
        repo.framework = g.framework

    languages = g.languages
    if languages:
        repo.languages = languages
        repo.language = g.language

    topics = g.topics
    if len(topics):
        repo.topics.clear()
        repo.topics.add(*topics)

    repo.save()


@app.task(max_retries=10, name='mlprior.articles.tasks.update_blog_post_info')
def update_blog_post_info(blogpost_id):
    blog_post = BlogPost.objects.get(id=blogpost_id)

    title, description, image = web_preview(blog_post.url)

    print(title)
    if title == 'Not Acceptable!':
        title = blog_post.url
        description = ''

    blog_post.title = title
    blog_post.description = description
    blog_post.image = image

    blog_post.save()


@app.task(max_retries=10, name='mlprior.articles.tasks.update_youtube_info')
def update_youtube_info(blogpost_id):
    blog_post = YouTube.objects.get(id=blogpost_id)

    title, description, image = web_preview(blog_post.url)

    print(title)
    if title == 'Not Acceptable!':
        title = blog_post.url
        description = ''

    blog_post.title = title
    blog_post.description = description
    blog_post.image = image

    blog_post.save()


@app.task(max_retries=10, name='mlprior.articles.tasks.update_reddit_info')
def update_reddit_info(blogpost_id):
    blog_post = Reddit.objects.get(id=blogpost_id)

    title, description, image = web_preview(blog_post.url)

    print(title)
    if title == 'Not Acceptable!':
        title = blog_post.url
        description = ''

    blog_post.title = title
    blog_post.description = description
    blog_post.image = image

    blog_post.save()


@app.task(max_retries=10, name='mlprior.articles.tasks.update_website_info')
def update_website_info(blogpost_id):
    blog_post = WebSite.objects.get(id=blogpost_id)

    title, description, image = web_preview(blog_post.url)

    print(title)
    if title == 'Not Acceptable!':
        title = blog_post.url
        description = ''

    blog_post.title = title
    blog_post.description = description
    blog_post.image = image

    blog_post.save()


@app.task(max_retries=10, name='mlprior.articles.tasks.update_slides_info')
def update_slides_info(blogpost_id):
    blog_post = Slides.objects.get(id=blogpost_id)

    title, description, image = web_preview(blog_post.url)

    print(title)
    if title == 'Not Acceptable!':
        title = blog_post.url
        description = ''

    blog_post.title = title
    blog_post.description = description
    blog_post.image = image

    blog_post.save()


@periodic_task(
    run_every=(crontab(day_of_month='1')),
    name="trigger_github_updates",
    ignore_result=True
)
def trigger_github_updates():
    print('Triggering update of all GitHubs')
    for github in GitHub.objects.all():
        update_github_info.delay(github.id, first_update=False)


#
#
# @app.task(name='mlprior.articles.tasks.trigger_resources_updates')
# def trigger_resources_updates():
#     print('trigger_resources_updates')
#     for blogpost in BlogPost.objects.all():
#         print(blogpost.url)
#         update_blog_post_info.delay(blogpost.id)
