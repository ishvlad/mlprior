

import base64
import re

from github import Github
from github.GithubException import GithubException

AVAILABLE_FRAMEWORKS = [
    'torch', 'tensorflow', 'theano', 'keras', 'caffe', 'chainer', 'cntk', 'mxnet'
]


N_FREQUENCY_OF_LIB_IN_CODE = 5


class GitHubRepo(object):
    api = Github("c0c86fd1d0073aa9e528e66d0ca32992ed50d8e4")

    @staticmethod
    def is_github_repo(url):
        expr = r'(http)?[s]?(://)?github\.com/[a-zA-Z0-9\_\-]+/[a-zA-Z0-9\_\-]+'
        res = re.search(expr, url)
        return res is not None

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
    def description(self):
        return self.repo.description or ''

    @property
    def topics(self):
        return self.repo.get_topics()

    @property
    def languages(self):
        git_languages = self.repo.get_languages()
        languages = {}

        if sum(git_languages.values()) == 0:
            return languages

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

        n_in_code = dict()

        contents = self.repo.get_contents("")
        while len(contents) > 1:
            file_content = contents.pop(0)

            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path))
            else:
                try:
                    current_file_code = str(base64.b64decode(file_content.content))
                except (GithubException, TypeError) as e:
                    #  too big file
                    continue

                for lib in AVAILABLE_FRAMEWORKS:
                    if lib not in n_in_code.keys():
                        n_in_code[lib] = 0
                    n_in_code[lib] += current_file_code.count(lib)

                for lib, freq in n_in_code.items():
                    if freq > N_FREQUENCY_OF_LIB_IN_CODE:
                        if lib == 'torch' and self.is_python():
                            # difference between pytorch and lua torch
                            return 'pytorch'
                        return lib

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
        'https://github.com/carpedm20/DCGAN-tensorflow',
        'https://github.com/junyanz/CycleGAN',
        'https://github.com/phillipi/pix2pix',
        'https://github.com/davidstutz/caffe-tools'
    ]:
        print(url)


        g = GitHubRepo(url)
        # print(g.arxiv_links)
        print(g.framework)
        print(g.licence)
        print(g.topics)
        print(g.description)
        # print(g.repo.get_stats_code_frequency())
    #
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(asyncio.wait(futures))


