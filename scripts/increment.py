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
                            NGramsSentence, NGramsMonth, SentenceVSMonth, ArticleText
from arxiv import ArXivArticle, ArXivAPI
from django.db.models import F, Q
from nltk import ngrams
from scripts.db_manager import DBManager
from urllib.request import urlopen
from utils.constants import GLOBAL__CATEGORIES
from utils.recommendation import RelationModel

import utils.logging

file_tag = str(datetime.datetime.now())
logger = utils.logging.get_logger('Increment_' + file_tag)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-download_meta', action='store_true', help='Do we need to download articles from arXiv?')
    parser.add_argument('-download_pdf', action='store_true', help='Do we need to download pdf?')
    parser.add_argument('-pdf2txt', action='store_true', help='Do we need to generate TXT?')
    parser.add_argument('-retrain', action='store_true', help='Do we need to retrain recommendation model?')
    parser.add_argument('-inner_vector', action='store_true', help='Do we need to calculate inner vectors?')

    parser.add_argument('--batch_size', type=int, help='Articles per iteration', default=100)
    parser.add_argument('--max_articles', type=int, help='number of data loading workers', default=200)
    parser.add_argument('--sleep_time', type=int, help='How much time of sleep (in sec) between API calls', default=5)

    args = parser.parse_args()
    return args


def overall_stats():
    articles = Article.objects
    logger.info('DATABASE stats:')
    logger.info('\tNumber of articles:                   %d' % articles.count())
    logger.info('\tNumber of articles with pdf:          %d' % articles.filter(has_pdf=True).count())
    logger.info('\tNumber of articles with txt:          %d' % articles.filter(has_txt=True).count())
    logger.info('\tNumber of articles with inner vector: %d' % articles.filter(has_inner_vector=True).count())
    logger.info('\tNumber of articles with neighbors:    %d' % articles.filter(has_neighbors=True).count())
    logger.info('\tNumber of articles with ngram stats:  %d' % articles.filter(has_ngram_stat=True).count())


def _get_max_articles(articles, max_articles):
    upper_bound = articles.count()
    if max_articles <= 0 or max_articles >= upper_bound:
        logger.info('There are %d articles. Take all' % max_articles)
        return upper_bound
    else:
        logger.info('There are %d articles. Take only %d of them' % (upper_bound, max_articles))
        return max_articles


@utils.logging.timeit(logger, 'Download Meta Time', level=logging.INFO)
def download_meta(args):
    logger.info('START downloading metas from arXiv')
    arxiv_api = ArXivAPI(args.sleep_time)
    db = DBManager()

    attempt = 1
    start = 0
    ok_list = []
    pbar = tqdm.tqdm(total=args.max_articles)

    while len(ok_list) < args.max_articles:
        logger.debug('BUFFER is empty. arXiv.API -- Try to get %d articles...' % args.batch_size)

        entries = arxiv_api.search(
            categories=['cat:' + c for c in GLOBAL__CATEGORIES],
            start=start, max_result=args.batch_size
        )
        logger.debug('... received %d articles from arXiv' % len(entries))

        start += args.batch_size
        if len(entries) == 0:
            start -= args.batch_size
            if attempt < 4:
                logger.debug('Empty buffer again. ArXiv is over :) Attempt %d.' % attempt)
                attempt += 1
            else:
                logger.debug('Empty buffer again. ArXiv is over :) Stop downloading.')
                break
        else:
            attempt = 1

        #####################
        #  Check existance  #
        #####################

        records = [ArXivArticle(x) for x in entries]

        records_idx = db.article_filter_by_existance([r.id for r in records])
        entries = list(np.array(records)[records_idx])

        if len(entries) != 0:
            logger.debug('There are %d new articles. Append to list' % len(entries))
            ok_list += entries
            for a in tqdm.tqdm(entries):
                db.add_article(a)
            pbar.update(len(entries))
        else:
            logger.debug('arXiv.API: no new articles')

    pbar.close()
    logger.info('FINISH downloading %d metas from arXiv' % len(ok_list))


@utils.logging.timeit(logger, 'Download PDF Time', level=logging.INFO)
def download_pdf(args, path_pdf='data/pdfs'):
    logger.info('START downloading PDFs from arXiv')

    articles = Article.objects.filter(has_pdf=False)
    max_articles = _get_max_articles(articles, args.max_articles)

    pbar = tqdm.tqdm(total=max_articles)
    ok_list = []
    for pk, idx, url in articles.values_list('pk', 'arxiv_id', 'url'):
        if len(ok_list) >= max_articles:
            break

        file_pdf = os.path.join(path_pdf, str(idx) + '.pdf')
        url += '.pdf'

        if os.path.exists(file_pdf) and os.path.getsize(file_pdf) != 0:
            logger.debug('PDF ' + idx + ' already exists. Just update flag')
            ok_list.append(pk)
            pbar.update(1)
            continue

        try:
            req = urlopen(url, None, args.sleep_time)
            with open(file_pdf, 'wb+') as fp:
                shutil.copyfileobj(req, fp)
            ok_list.append(pk)
            pbar.update(1)
        except Exception as e:
            logger.debug(idx + ' (' + url + '): Cannot download PDF. Exception: ' + e)

    pbar.close()
    logger.info('FINISH downloading PDFs from arXiv. Now update flags of %d articles' % len(ok_list))
    if len(ok_list) != 0:
        Article.objects.filter(pk__in=ok_list).update(has_pdf=True)


@utils.logging.timeit(logger, 'PDF 2 TXT Time', level=logging.INFO)
def pdf2txt(args, path_pdf='data/pdfs', path_txt='data/txts'):
    logger.info('START generating TXTs from PDFs')
    db = DBManager()

    articles = Article.objects.filter(Q(has_pdf=True) & Q(has_txt=False))
    max_articles = _get_max_articles(articles, args.max_articles)

    pbar = tqdm.tqdm(total=max_articles)
    ok_list = []
    new_items = []
    for pk, idx in articles.values_list('pk', 'arxiv_id'):
        if len(ok_list) >= max_articles:
            break

        file_pdf = os.path.join(path_pdf, idx + '.pdf')
        file_txt = os.path.join(path_txt, idx + '.txt')

        if os.path.exists(file_txt) and os.path.getsize(file_txt) != 0:
            arts = ArticleText.objects.filter(article_origin=pk).values('text')

            if len(arts) != 0 and arts[0]['text'] is not None:
                logger.debug('TXT ' + idx + ' already exists. Just update flag')
                ok_list.append(pk)
                pbar.update(1)
                continue
            else:
                logger.debug('TXT ' + idx + ' already exists, but text not appears in DB. Save text')
        else:
            cmd = "pdftotext %s %s 2> logs/pdf2txt_%s.log" % (file_pdf, file_txt, idx)
            os.system(cmd)

            if not os.path.isfile(file_txt) or os.path.getsize(file_txt) == 0:
                logger.debug(idx + '. pdf2txt: Failed to generate TXT (No .txt file)). NEXT')
                continue

        with open(file_txt, 'r') as f:
            text = ' '.join(f.readlines())[:100000]

        new_items.append(ArticleText(
            article_origin_id=pk,
            pdf_location=file_pdf,
            txt_location=file_txt,
            text=text
        ))
        ok_list.append(pk)
        pbar.update(1)

    pbar.close()
    logger.info('FINISH generating TXTs. Now update flags of %d articles' % len(ok_list))
    if len(ok_list) != 0:
        db.bulk_create(new_items)
        Article.objects.filter(pk__in=ok_list).update(has_txt=True)


@utils.logging.timeit(logger, 'Retraining model Time', level=logging.INFO)
def retrain(args):
    logger.info('START Retraining model')

    articles = Article.objects.filter(has_txt=True)
    max_articles = _get_max_articles(articles, args.max_articles)

    model = RelationModel()
    model.retrain(logger, train_size=max_articles)

    logger.info('Training is finished. Set all flags to False')
    Article.objects.update(has_inner_vector=False)
    Article.objects.update(has_neighbors=False)
    logger.info('FINISH Retraining model')


@utils.logging.timeit(logger, 'Calculate Inner Vector Time', level=logging.INFO)
def calc_inner_vector(args):
    logger.info('START making relations')
    db = DBManager()
    model = RelationModel()

    if model.trained is False:
        logger.info("Relation model not trained. Let's train first (-retrain).")
        return

    articles = Article.objects.filter(Q(has_txt=True) & Q(has_inner_vector=False))
    max_articles = _get_max_articles(articles, args.max_articles)

    articles = articles.values('id', 'title', 'abstract', 'articletext__text')[:max_articles]
    articles = pd.DataFrame(articles)
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
    db.bulk_create(items)
    Article.objects.filter(pk__in=list(articles.id.values)).update(has_inner_vector=True)
    logger.info('FINISH making relations')


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


@utils.logging.timeit(logger, 'Stacked bar Time', level=logging.INFO)
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


@utils.logging.timeit(logger, 'Trend Ngrams Time', level=logging.INFO)
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


@utils.logging.timeit(logger, 'Total Time', level=logging.INFO)
def main(args):
    path, path_pdf, path_txt = 'data', 'data/pdfs', 'data/txts'
    for d in [path, path_pdf, path_txt]:
        if not os.path.exists(d):
            os.mkdir(d)

    overall_stats()

    if args.download_meta:
        download_meta(args)

    if args.download_pdf:
        download_pdf(args, path_pdf)

    if args.pdf2txt:
        pdf2txt(args, path_pdf, path_txt)

    if args.retrain:
        retrain(args)

    if args.inner_vector:
        calc_inner_vector(args)

    # articles = relations(articles_id)
    # visualizations(articles)

    logger.debug('#'*50)
    overall_stats()
    logger.debug('#'*50)


if __name__ == '__main__':
    args = parse_args()
    main(args)

