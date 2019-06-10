import re

from mlprior.settings import API_HOST
import requests


def send_github_url_to_server(url, arxiv_id):
    """

    :param url: Link to the GitHub repository
    :param arxiv_id: in form '1706.03762'
    :return:
    """
    res = requests.post(API_HOST + 'api/githubs/', data={
            'url': url,
            'arxiv_id': arxiv_id
        })

    return res.text


def find_github_repo_in_text(text):
    expr = r'(http)?[s]?(://)?github\.com/[a-z0-9]+/[a-z0-9]+'
    res = re.search(expr, text)
    if res is None:
        return None
    return res[0]



