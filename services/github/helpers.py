import aiohttp
from mlprior.settings import API_HOST
import requests

# async def send_github_url_to_server(url, arxiv_id):
#     """
#     Sends github url and attach it to the article
#     :param url: link to GitHub repository
#     :param article_id: id of the article in the DB
#     :return:
#     """
#
#     async with aiohttp.ClientSession() as session:
#         async with session.post(API_HOST + 'articles/api/githubs/', data={
#             'url': url,
#             'arxiv_id': arxiv_id
#         }) as response:
#             data = await response.text()
#             print(data)
#             return data


def send_github_url_to_server(url, arxiv_id):
    print(API_HOST)
    res = requests.post(API_HOST + 'articles/api/githubs/', data={
            'url': url,
            'arxiv_id': arxiv_id
        })

    print(res.text)

    return res.text