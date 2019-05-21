import sys

import asyncio

sys.path.append('./')

from services.github.helpers import send_github_url_to_server
import json


with open('./scripts/links-between-papers-and-code.json', 'r') as f:
    data = json.load(f)

futures = []

for i in range(len(data)):
    print('Add GitHub for', data[i]['paper_arxiv_id'])

    futures.append(send_github_url_to_server(data[i]['repo_url'], data[i]['paper_arxiv_id']))

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(futures))
