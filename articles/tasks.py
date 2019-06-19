from github import UnknownObjectException

from articles.models import GitHubRepository, GitHubInfo, BlogPost, BlogPostInfo
from mlprior.celery import app
from services.github.repository import GitHubRepo
from webpreview import web_preview


@app.task(max_retries=10, name='mlprior.articles.tasks.update_github_info', rate_limit='100/h')
def update_github_info(github_id):
    repo = GitHubRepository.objects.get(id=github_id)

    url = repo.url

    try:
        g = GitHubRepo(url)
    except UnknownObjectException as e:
        print("The repository doesn't exist")
        return

    github_info, is_created = GitHubInfo.objects.get_or_create(
        repo_id=repo.id
    )

    print(g.name)
    github_info.title = g.name
    github_info.n_stars = g.n_stars
    github_info.framework = g.framework
    github_info.description = g.description

    languages = g.languages
    if languages:
        github_info.languages = languages
        github_info.language = g.language

    topics = g.topics
    if len(topics):
        github_info.topics.add(*topics)

    github_info.save()


@app.task(max_retries=10, name='mlprior.articles.tasks.update_blog_post_info')
def update_blog_post_info(blogpost_id):
    print('zopa!!!!')
    blog_post = BlogPost.objects.get(id=blogpost_id)

    title, description, image = web_preview(blog_post.url)

    print(title)
    if title == 'Not Acceptable!':
        title = blog_post.url
        description = ''

    blogpost_info, is_created = BlogPostInfo.objects.get_or_create(
        blog_post_id=blog_post.id
    )

    blogpost_info.title = title
    blogpost_info.description = description
    blogpost_info.image = image

    blogpost_info.save()


@app.task(name='mlprior.articles.tasks.trigger_github_updates')
def trigger_github_updates():
    print('trigger_github_updates')
    for github in GitHubRepository.objects.all():
        print(github.url)
        update_github_info.delay(github.id)


@app.task(name='mlprior.articles.tasks.trigger_resources_updates')
def trigger_resources_updates():
    print('trigger_resources_updates')
    for blogpost in BlogPost.objects.all():
        print(blogpost.url)
        update_blog_post_info.delay(blogpost.id)
