import sys

sys.path.append('./')

from services.github.helpers import send_github_url_to_server
import json

with open('./scripts/links-between-papers-and-code.json', 'r') as f:
    data = json.load(f)

futures = []

for i in range(len(data)):
    print('Add GitHub for', data[i]['paper_arxiv_id'], 'url:', data[i]['repo_url'])
    if data[i]['paper_arxiv_id'] is None:
        print('Skipping None')
        continue
    res = send_github_url_to_server(data[i]['repo_url'], data[i]['paper_arxiv_id'])

    print(res)

