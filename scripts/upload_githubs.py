import sys

import asyncio

sys.path.append('./')

from services.github.helpers import send_github_url_to_server
import json
from time import sleep


with open('./scripts/links-between-papers-and-code.json', 'r') as f:
    data = json.load(f)

futures = []

for i in range(len(data)):
    print('Add GitHub for', data[i]['paper_arxiv_id'])
    if data[i]['paper_arxiv_id'] is None:
        print('Skipping None')
        continue
    futures.append(send_github_url_to_server(data[i]['repo_url'], data[i]['paper_arxiv_id']))

# loop = asyncio.get_event_loop()
# loop.run_until_complete(asyncio.wait(futures))
