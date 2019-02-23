import argparse
import logging
import numpy as np
import os
import shutil
import sys
import time
import tqdm


sys.path.append('./')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import django

django.setup()

from arxiv import ArXivArticle, ArXivAPI
from scripts.db_manager import DBManager
from urllib.request import urlopen
from utils.constants import GLOBAL__CATEGORIES

import utils.logging
logger = utils.logging.get_logger('Increment')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--article_per_it', type=int, help='Articles per iteration', default=1000)
    parser.add_argument('--max_articles', type=int, help='number of data loading workers', default=1000)
    parser.add_argument('--sleep_time', type=int, help='How much time of sleep (in sec) between API calls', default=5)

    args = parser.parse_args()
    return args


@utils.logging.timed(logger, 'Download Articles Time')
def download_articles(args):
    time.sleep(1)
    # arxiv_api = ArXivAPI(args.sleep_time)
    # db = DBManager()
    #
    # path, path_pdf, path_txt = 'data', 'data/pdfs', 'data/txts'
    # for d in [path, path_pdf, path_txt]:
    #     if not os.path.exists(d):
    #         os.mkdir(d)
    #
    # num_from_arxiv = 0
    # num_pdfs_generated = 0
    # num_txts_parsed = 0
    # ok_list = []
    #
    # start = 0
    # entries = []
    # pbar = tqdm.tqdm(total=args.max_articles)
    #
    # while len(ok_list) < args.max_articles:
    #     while len(entries) == 0:
    #         entries = arxiv_api.search(
    #             categories=['cat:' + c for c in GLOBAL__CATEGORIES],
    #             start=start, max_result=args.article_per_it
    #         )
    #
    #         start += args.article_per_it
    #         if len(entries) == 0:
    #             start -= args.article_per_it
    #             print(logger.log('ArXiv is over :)'))
    #             break
    #
    #         #####################
    #         #  Check existance  #
    #         #####################
    #
    #         records = [ArXivArticle(x) for x in entries]
    #
    #         records_idx = db.article_filter_by_existance([r.id for r in records])
    #         entries = list(np.array(records)[records_idx])
    #
    #     arxiv_article = entries.pop()
    #     url, idx = arxiv_article.pdf_url, arxiv_article.id
    #     num_from_arxiv += 1
    #
    #     if not url:
    #         # print('PDF not exists %s' % idx)
    #         errors_idx.append('WARNING: ' + idx + ' (No url)')
    #         continue
    #
    #     ##############
    #     # Create PDF #
    #     ##############
    #     file_pdf = os.path.join(path_pdf, idx + '.pdf')
    #     url += '.pdf'
    #
    #     if not (os.path.exists(file_pdf) and os.path.getsize(file_pdf) != 0):
    #         try:
    #             req = urlopen(url, None, args.sleep_time)
    #
    #             with open(file_pdf, 'wb+') as fp:
    #                 shutil.copyfileobj(req, fp)
    #
    #             num_pdfs_generated += 1
    #         except:
    #             errors_idx.append('ERROR: ' + idx + ' (Cannot download PDF)')
    #             continue
    #     else:
    #         errors_idx.append(idx + ' (PDF exists)')
    #
    #     ##############
    #     # Create TXT #
    #     ##############
    #     file_txt = os.path.join(path_txt, idx + '.txt')
    #
    #     if not (os.path.exists(file_txt) and os.path.getsize(file_txt) != 0):
    #         cmd = "pdftotext %s %s 2> log.txt" % (file_pdf, file_txt)
    #         os.system(cmd)
    #
    #         if not os.path.isfile(file_txt):
    #             # print('error downloading pdf: ', idx)
    #             errors_idx.append('ERROR: ' + idx + ' (Failed to generate txt)')
    #             continue
    #
    #         num_txts_parsed += 1
    #     else:
    #         errors_idx.append(idx + ' (TXT exists)')
    #
    #     with open(file_txt, 'r') as f:
    #         text = ' '.join(f.readlines())[:100000]
    #
    #     ################
    #     # Saving to DB #
    #     ################
    #     article_id = db.add_article(arxiv_article)
    #     db.add_article_text(article_id, file_pdf, file_txt, text)
    #     ok_list.append(article_id)
    #     pbar.update(1)
    #
    # pbar.close()
    #
    # result_str = 'Requested %d articles\n' % start
    # result_str += "Get %d articles' meta from arxiv\n" % num_from_arxiv
    # result_str += 'Generate %d PDFs\n' % num_pdfs_generated
    # result_str += 'Generate %d TXTs\n' % num_txts_parsed
    # result_str += 'Append %d articles\n' % len(ok_list)
    # print(result_str)
    # result_str += '#' * 50 + '\n'
    # result_str += 'Log:\n' + '\n'.join(errors_idx)


    return [] #ok_list, result_str



if __name__ == '__main__':
    args = parse_args()
    # total_start_time = time()

    # tag = 'Download from arXiv'
    # logger.start_timer(tag)
    articles_ids = download_articles(args)
    logger.debug('AAA')
    logger.info('BBB')
    logger.warning('CCC')
    logger.error('DDD')
    # print(logger.log_time(tag))

    # tag = 'Make relations'
    # logger.start_timer(tag)
    # articles_ids = download_articles(args, logger)
    # print(logger.log_time(tag))

