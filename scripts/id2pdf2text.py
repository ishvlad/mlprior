import os
import random
import sys
import shutil
import time
import tqdm

sys.path.append('./')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import django

django.setup()

from urllib.request import urlopen
from articles.models import Article

if __name__ == '__main__':
    path, path_pdf, path_txt = 'data', 'data/pdfs', 'data/txts'


    for d in [path, path_pdf, path_txt]:
        if not os.path.exists(d):
            os.mkdir(d)

    print('START Downloading pdfs')

    timeout_secs = 10
    articles = Article.objects.all().values('url', 'id')
    for x in tqdm.tqdm(articles):
        url, idx = x['url'], x['id']
        name = url.split('/')[-1] + '_' + str(idx) + '.pdf'
        name = os.path.join(path_pdf, name)
        url += '.pdf'

        if os.path.exists(name) and os.path.getsize(name) != 0:
            continue

        try:
            req = urlopen(url, None, timeout_secs)

            with open(name, 'wb+') as fp:
                shutil.copyfileobj(req, fp)
            time.sleep(0.05 + random.uniform(0, 0.1))
        except Exception as e:
            print('error downloading: ', url)
            print(e)

    d = {}

    print('START Extracting text')
    for name in tqdm.tqdm(os.listdir(path_pdf)):
        idx = int(name.split('_')[1][:-4])
        name_from = os.path.join(path_pdf, name)
        name_to = os.path.join(path_txt, name[:-4] + '.txt')

        if os.path.exists(name) and os.path.getsize(name) != 0:
            continue

        cmd = "pdftotext %s %s" % (name_from, name_to)
        os.system(cmd)

        if not os.path.isfile(name_to):
            print('there was a problem with parsing %s to text, creating an empty text file.' % (name_to,))

        time.sleep(0.01)










