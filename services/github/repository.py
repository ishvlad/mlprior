

from github import Github
from github.GithubException import GithubException
import base64
import re
import asyncio

from services.github.helpers import send_github_url_to_server

NAME_PYTORCH = 'PyTorch'
NAME_TENSORFLOW = 'TensorFlow'
NAME_THEANO = 'Theano'

N_FREQUENCY_OF_LIB_IN_CODE = 5


class GitHubRepo(object):
    api = Github("c0c86fd1d0073aa9e528e66d0ca32992ed50d8e4")

    @staticmethod
    def get_name(url):
        return url.replace('https://github.com/', '').replace('http://github.com/', '').replace('github.com/', '')

    def __init__(self, url):
        name = self.get_name(url)
        self.repo = self.api.get_repo(full_name_or_id=name)

    @property
    def name(self):
        return self.repo.name

    @property
    def languages(self):
        git_languages = self.repo.get_languages()
        languages = {}

        factor = 1.0 / sum(git_languages.values())
        for k in git_languages:

            percent = int(git_languages[k] * factor * 100)
            if percent < 1:
                continue
            languages[k] = percent

        return languages

    @property
    def language(self):
        return self.repo.language

    @property
    def n_stars(self):
        return self.repo.stargazers_count

    @property
    def all_code(self):
        all_code = []

        contents = self.repo.get_contents("")
        while len(contents) > 1:
            file_content = contents.pop(0)

            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path))
            else:
                all_code.append(str(base64.b64decode(file_content.content)))

        return ' '.join(all_code)

    def is_python(self):
        return self.languages.get('Python', 0) > 0.25

    @property
    def framework(self):
        # code = self.all_code

        n_in_code = dict(
            torch=0,
            tensorflow=0,
            theano=0
        )

        contents = self.repo.get_contents("")
        while len(contents) > 1:
            file_content = contents.pop(0)

            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path))
            else:
                try:
                    current_file_code = str(base64.b64decode(file_content.content))
                except GithubException as e:
                    #  too big file
                    continue
                n_in_code['torch'] += current_file_code.count('torch')
                n_in_code['tensorflow'] += current_file_code.count('tensorflow')
                n_in_code['theano'] += current_file_code.count('theano')

                print(n_in_code)

                if n_in_code['torch'] > N_FREQUENCY_OF_LIB_IN_CODE:
                    return NAME_PYTORCH
                if n_in_code['tensorflow'] > N_FREQUENCY_OF_LIB_IN_CODE:
                    return NAME_TENSORFLOW
                if n_in_code['theano'] > N_FREQUENCY_OF_LIB_IN_CODE:
                    return NAME_THEANO

        return ''


    @property
    def arxiv_links(self):
        readme = self.repo.get_contents('README.md')
        readme = str(base64.b64decode(readme.content))
        print(readme)

        urls = re.search('http[s]?://arxiv\.org/(pdf|abs)/[0-9]+\.[0-9]+', readme)
        print(urls.group())
        return urls



if __name__ == '__main__':
    # or using an access token

    futures = []

    for url in [
        'https://github.com/jadore801120/attention-is-all-you-need-pytorch',
        'https://github.com/connor11528/angular-drf-todolist',
        'https://github.com/Theano/Theano',
        'https://github.com/carpedm20/DCGAN-tensorflow'
    ]:
        print(url)

        futures.append(send_github_url_to_server(url, 101))

        # g = GitHubRepo(url)
        # print(g.arxiv_links)
        # print(g.framework)
        # print(g.repo.get_stats_code_frequency())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(futures))


