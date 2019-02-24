import argparse
import datetime
import logging
import numpy as np
import operator
import os
import pandas as pd
import re
import shutil
import sys
import tqdm

sys.path.append('./')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

import django

django.setup()

from articles.models import Article, ArticleVector, ArticleArticleRelation, \
                            CategoriesVSDate, Categories, CategoriesDate, \
                            NGramsSentence, NGramsMonth, SentenceVSMonth
from arxiv import ArXivArticle, ArXivAPI
from django.db.models import F
from nltk import ngrams
from scripts.db_manager import DBManager
from urllib.request import urlopen
from utils.constants import GLOBAL__CATEGORIES
from utils.recommendation import RelationModel

import utils.logging

logger = utils.logging.get_logger('Increment_' + str(datetime.datetime.now()))

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--article_per_it', type=int, help='Articles per iteration', default=200)
    parser.add_argument('--max_articles', type=int, help='number of data loading workers', default=1000)
    parser.add_argument('--sleep_time', type=int, help='How much time of sleep (in sec) between API calls', default=5)

    args = parser.parse_args()
    return args


@utils.logging.timeit(logger, 'Download Articles Time', level=logging.WARNING)
def download_articles(args):
    logger.info('START downloading')
    arxiv_api = ArXivAPI(args.sleep_time)
    db = DBManager()

    path, path_pdf, path_txt = 'data', 'data/pdfs', 'data/txts'
    for d in [path, path_pdf, path_txt]:
        if not os.path.exists(d):
            os.mkdir(d)

    num_from_arxiv = 0
    num_pdfs_generated = 0
    num_txts_parsed = 0
    ok_list = []

    start = 0
    entries = []
    pbar = tqdm.tqdm(total=args.max_articles)

    while len(ok_list) < args.max_articles:
        while len(entries) == 0:
            logger.debug('BUFFER is empty. arXiv.API -- Get %d articles' % args.article_per_it)

            entries = arxiv_api.search(
                categories=['cat:' + c for c in GLOBAL__CATEGORIES],
                start=start, max_result=args.article_per_it
            )
            logger.debug('Obtain %d articles' % len(entries))

            start += args.article_per_it
            if len(entries) == 0:
                start -= args.article_per_it
                logger.info('ArXiv is over :) Stop Downloading.')
                break

            #####################
            #  Check existance  #
            #####################

            records = [ArXivArticle(x) for x in entries]

            records_idx = db.article_filter_by_existance([r.id for r in records])
            entries = list(np.array(records)[records_idx])

            if len(entries) != 0:
                logger.debug('arXiv.API: %d articles are new' % len(entries))

        if len(entries) == 0:
            break
        arxiv_article = entries.pop()
        url, idx = arxiv_article.pdf_url, arxiv_article.id
        num_from_arxiv += 1

        if not url:
            logger.debug(idx + ': (No url). NEXT')
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

                num_pdfs_generated += 1
            except:
                logger.warning(idx + ' (Cannot download PDF). NEXT')
                continue
        else:
            logger.debug(idx + ': (PDF exists). Continue processing ' + idx)

        ##############
        # Create TXT #
        ##############
        file_txt = os.path.join(path_txt, idx + '.txt')

        if not (os.path.exists(file_txt) and os.path.getsize(file_txt) != 0):
            cmd = "pdftotext %s %s 2> log.txt" % (file_pdf, file_txt)
            os.system(cmd)

            if not os.path.isfile(file_txt):
                logger.warning(idx + ' (Failed to generate TXT). NEXT')
                continue

            num_txts_parsed += 1
        else:
            logger.debug(idx + ': (TXT exists). Continue processing ' + idx)

        with open(file_txt, 'r') as f:
            text = ' '.join(f.readlines())[:100000]

        ################
        # Saving to DB #
        ################
        article_id = db.add_article(arxiv_article)
        db.add_article_text(article_id, file_pdf, file_txt, text)
        ok_list.append(article_id)
        pbar.update(1)
        logger.debug(idx + ': OK. NEXT')

    pbar.close()

    logger.debug('#' * 50)
    logger.info('FINISH. Statistics:')
    logger.info('\tRequested %d articles' % start)
    logger.info("\tGet %d articles' meta from arxiv" % num_from_arxiv)
    logger.info('\tGenerate %d PDFs' % num_pdfs_generated)
    logger.info('\tGenerate %d TXTs' % num_txts_parsed)
    logger.info('\tAppend %d articles' % len(ok_list))
    logger.debug('#' * 50)

    return ok_list


@utils.logging.timeit(logger, 'Make Relation Time')
def relations(articles_id, n_neighbors=21):
    logger.info('START making relations')
    db = DBManager()

    logger.debug('Loading %d articles' % len(articles_id))
    articles = Article.objects.filter(pk__in=articles_id).values('id', 'date', 'category', 'title', 'abstract', 'articletext__text')
    articles = pd.DataFrame(articles)
    assert len(articles_id) == len(articles)

    logger.debug('Feature engineering')
    model = RelationModel()
    features = model.get_features(
        articles.title.values,
        articles.abstract.values,
        articles.articletext__text.values,
    )

    logger.debug('Saving features (len: %d)' % len(features))
    items = []
    for idx, feature in zip(articles.id.values, features):
        items.append(ArticleVector(
            article_origin_id=idx,
            inner_vector=feature.tobytes()
        ))
    db.bulk_create(items, batch_size=5000)

    logger.debug('Obtain ' + str(n_neighbors-1) + ' neighbors')
    new_tuples, old_tuples = model.get_knn_dist(articles.id.values, features, n_neighbors)
    logger.info('Processed %d new articles. Also need to update %d old articles' % (len(new_tuples)/(n_neighbors-1),len(old_tuples)))

    if len(old_tuples) > 0:
        logger.debug('Update old articles')
        ArticleArticleRelation.objects.filter(left_id__in=[x[0] for x in old_tuples]).delete()
        for x in old_tuples:
            new_tuples.extend(x)

    logger.info('Saving relations (len: %d)' % len(new_tuples))
    items = []
    for i_left, i_right, distance in tqdm.tqdm(new_tuples):
        items.append(ArticleArticleRelation(
            left_id=i_left,
            right_id=i_right,
            distance=distance
        ))
    db.bulk_create(items, batch_size=5000)

    logger.debug('#' * 50)
    logger.info('FINISH. Statistics:')
    logger.info('\tNew: %d articles (%d relations)' % (len(articles), len(articles)*(n_neighbors-1)))
    logger.info('\tUpdated %d articles (%d relations)' % (len(old_tuples), len(old_tuples)*(n_neighbors-1)))
    logger.debug('#' * 50)

    return articles


def get_grams_dict(sentences, max_ngram_len=5):
    # stop_words = [
    #     'a', 'the', 'in', 'of', 'in', 'this', 'and',
    #     'to', 'we', 'for', 'is', 'that', 'on', 'with'
    #     'are', 'by', 'as', 'an', 'from', 'our', 'be'
    # ]

    p = re.compile('\w+[\-\w+]*', re.IGNORECASE)
    dic = [{} for _ in range(max_ngram_len)]

    key_store = []

    for n in range(1, max_ngram_len + 1):
        for s in sentences:
            grams = ngrams(p.findall(s.lower()), n)

            for key in set(grams):
                # miss = False
                # for sw in stop_words:
                #     if sw in key:
                #         miss = True
                #         break
                # if miss:
                #     continue

                key = ' '.join(key)
                if key in dic[n - 1]:
                    dic[n - 1][key] += 1
                else:
                    dic[n - 1][key] = 1
                key_store.append(key)

    return dic, key_store

@utils.logging.timeit(logger, 'Stacked bar Time', level=logging.WARNING)
def stacked_bar(articles):
    db = DBManager()
    articles['date'] = pd.to_datetime(articles['date'])

    logger.info('START Stacked bar')

    new_months = []
    logger.debug('Looking for new months')
    for date in articles.date:
        date_code = date.month + date.year * 100
        if CategoriesDate.objects.filter(date_code=date_code).count() == 0:
            logger.debug('Append new date: ' + str(date_code))

            new_date, _ = CategoriesDate.objects.update_or_create(date_code=date_code, date=date.strftime('%b %y'))
            new_date.save()

            db.bulk_create([CategoriesVSDate(
                category=c,
                from_month=new_date,
                count=0
            ) for c in Categories.objects.all()])

            new_months.append(str(date_code))
    if len(new_months) != 0:
        logger.info('Append new months: ' + ' '.join(new_months))
    else:
        logger.info('No new months')

    new_cats = []
    logger.debug('Looking for new categories')
    for cat in articles.category.values:
        if Categories.objects.filter(category=cat).count() == 0:
            logger.critical('Category does not exists: ' + cat + '. Specify full and append to GLOBAL!!!!')
            new_category, _ = Categories.objects.update_or_create(category=cat, category_full='NOT SPECIFIED')
            new_category.save()
            new_cats.append(cat)

            db.bulk_create([CategoriesVSDate(
                from_category=new_category,
                from_month=d,
                count=0
            ) for d in CategoriesDate.objects.all()])
    if len(new_months) != 0:
        logger.info('Append new categories: ' + ' '.join(new_cats))
    else:
        logger.info('No new categories')

    new_vs = 0
    logging.debug('Update bar counts')
    for cat, date in tqdm.tqdm(zip(articles.category.values, articles.date)):
        date_code = date.month + date.year * 100
        target = CategoriesVSDate.objects.filter(
            from_category__category=cat,
            from_month__date_code=date_code
        )
        assert target.count() == 1
        target.update(count=F('count') + 1)
        new_vs += 1

    logger.info('FINISH Stacked bar. Statictics:')
    logger.info('\t%d new categories (SPECIFY!): ' % len(new_cats))
    logger.info('\t%d new dates: ' % len(new_months))
    logger.info('\tTotal %d updates' % new_vs)


@utils.logging.timeit(logger, 'Trend Ngrams Time', level=logging.WARNING)
def trend_ngrams(articles, max_n_for_grams=3):
    db = DBManager()
    articles['date'] = pd.to_datetime(articles['date'])
    articles['idx_sort'] = articles.date.dt.month + articles.date.dt.year * 100
    articles.sort_values('idx_sort', inplace=True)
    grouped = sorted(articles.groupby('idx_sort'), key=operator.itemgetter(0))

    logger.info('START Trend Ngrams')
    num_new = [0, 0, 0]
    num_update = 0
    for i_group, (date, df_group) in enumerate(grouped):

        logger.info('%d (%d out of %d)' % (date, i_group+1, len(grouped)))

        dics_ttl, keys_ttl = get_grams_dict(df_group.title.values, max_n_for_grams)
        dics_abs, keys_abs = get_grams_dict(df_group.abstract.values, max_n_for_grams)
        dics_txt, keys_txt = get_grams_dict(df_group.articletext__text.values, max_n_for_grams)
        keys = list(set(np.concatenate((keys_ttl, keys_abs, keys_txt))))

        upd = 0
        new_months, new_sentences, new_links = 0, 0, []

        if NGramsMonth.objects.filter(label_code=date).count() == 0:
            label = datetime.date(date//100, date%100, 1).strftime('%b %y')
            db.bulk_create([NGramsMonth(
                label_code=date,
                label=label,
                length=i+1
            ) for i in range(max_n_for_grams)])
            new_months += 1

        existed_keys = list(NGramsSentence.objects.filter(sentence__in=keys).values_list(flat=True))
        new_keys = np.array(keys)[~np.in1d(keys, existed_keys)]
        new_sentences = len(new_keys)
        db.bulk_create([NGramsSentence(sentence=k) for k in new_keys])

        for key in tqdm.tqdm(keys):
            length = len(key.split())

            sentence = NGramsSentence.objects.filter(sentence=key)[0]
            month = NGramsMonth.objects.filter(length=length, label_code=date)[0]

            base = SentenceVSMonth.objects.filter(from_corpora=month, from_item=sentence)
            if base.count() == 0:
                new_links.append(SentenceVSMonth(
                    from_corpora=month,
                    from_item=sentence,
                    freq_title=dics_ttl[length-1].get(key, 0),
                    freq_abstract=dics_abs[length-1].get(key, 0),
                    freq_text=dics_txt[length-1].get(key, 0),
                ))
            else:
                base.update(
                    freq_title=F('freq_title') + dics_ttl[length - 1].get(key, 0),
                    freq_abstract=F('freq_abstract') + dics_abs[length - 1].get(key, 0),
                    freq_text=F('freq_text') + dics_txt[length - 1].get(key, 0),
                )
                upd += 1

        start_str = '%d: ' % date
        num_new[0] += new_months
        num_new[1] += new_sentences
        logger.info(start_str + '{} new months, {} new sentences'.format(new_months, new_sentences))

        num_new[2] += len(new_links)
        num_update += upd
        logger.info(start_str + '{} new, {} updated'.format(len(new_links), upd))
        db.bulk_create(new_links)

    logger.info('FINISH Trend Ngrams. Statictics:')
    logger.info('\tNew months: %d' % num_new[0])
    logger.info('\tNew sentences: %d' % num_new[1])
    logger.info('\tNew links: %d' % num_new[2])
    logger.info('\tUpdated links: %d' % num_update)
    logger.debug('#'*50 + '\n')


def visualizations(articles, max_n_for_grams=3):
    logger.info('START Visualizations')

    stacked_bar(articles)
    trend_ngrams(articles, max_n_for_grams)

    logger.info('FINISH Visualization')


@utils.logging.timeit(logger, 'Total Time', level=logging.WARNING)
def main(args):
    articles_id = download_articles(args)
    articles = relations(articles_id)
    visualizations(articles)


if __name__ == '__main__':
    args = parse_args()
    main(args)

