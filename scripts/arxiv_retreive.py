import argparse
import os
import shutil
import sys
from time import time
import tqdm

from scripts.db_manager import DBManager

sys.path.append('./')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import django

django.setup()

from arxiv import ArXivArticle, ArXivAPI
from urllib.request import urlopen
from utils.constants import GLOBAL__CATEGORIES


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--article_per_it', type=int, help='Articles per iteration', default=50)
    parser.add_argument('--n_articles', type=int, help='number of data loading workers', default=1000)
    parser.add_argument('--sleep_time', type=int, help='How much time of sleep (in sec) between API calls', default=5)

    args = parser.parse_args()
    return args


def main(args):
    arxiv_api = ArXivAPI(args.sleep_time)
    db = DBManager()

    path, path_pdf, path_txt = 'data', 'data/pdfs', 'data/txts'
    for d in [path, path_pdf, path_txt]:
        if not os.path.exists(d):
            os.mkdir(d)

    errors_idx = []
    num_ok = 0

    start = 0
    entries = []

    for num_all in tqdm.trange(args.n_articles):
        if len(entries) == 0:
            entries = arxiv_api.search(
                categories=['cat:' + c for c in GLOBAL__CATEGORIES],
                start=start, max_result=args.article_per_it
            )

            start += args.article_per_it
            if len(entries) == 0:
                break

        record = entries.pop()
        arxiv_article = ArXivArticle(record)
        url, idx = arxiv_article.pdf_url, arxiv_article.id

        if not url:
            # print('PDF not exists %s' % idx)
            errors_idx.append(idx + ' (URL)')
            continue

        ##############
        # Create PDF #
        ##############
        file_pdf = os.path.join(path_pdf, idx + '.pdf')
        url += '.pdf'

        if not (os.path.exists(file_pdf) and os.path.getsize(file_pdf) != 0):
            try:
                req = urlopen(url, None, args.sleep_time)

                with open(file_pdf, 'wb+') as fp:
                    shutil.copyfileobj(req, fp)
            except Exception as e:
                # print('error downloading pdf: ', idx)
                errors_idx.append(idx + ' (PDF)')
                continue

        ##############
        # Create TXT #
        ##############
        file_txt = os.path.join(path_txt, idx + '.txt')

        if not (os.path.exists(file_txt) and os.path.getsize(file_txt) != 0):
            cmd = "pdftotext %s %s 2> log.txt" % (file_pdf, file_txt)
            os.system(cmd)

            if not os.path.isfile(file_txt):
                # print('error downloading pdf: ', idx)
                errors_idx.append(idx + ' (TXT)')
                continue

        with open(file_txt, 'r') as f:
            text = ' '.join(f.readlines())[:100000]

        ################
        # Saving to DB #
        ################
        article_id = db.add_article(arxiv_article)
        db.add_article_text(article_id, file_pdf, file_txt, text)

        num_ok += 1

    print('Downloaded %d/%d files' % (num_ok, num_all+1))
    print('Error IDX: ', errors_idx)


if __name__ == '__main__':
    args = parse_args()
    total_start_time = time()
    main(args)

    print('Total Time, min:', (time() - total_start_time) / 60)
