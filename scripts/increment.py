import argparse
import datetime
import logging
import numpy as np
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
from dateutil.relativedelta import relativedelta
from django.db.models import F, Q
from nltk import ngrams
from sklearn.neighbors import NearestNeighbors
from utils.db_manager import DBManager
from urllib.request import urlopen
from utils.constants import GLOBAL__CATEGORIES
from utils.recommendation import RelationModel

import log.logging

file_tag = str(datetime.datetime.now())
logger = log.logging.get_logger('Increment_' + file_tag)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-clean', action='store_true', help='pdf, txt, inner_vector, knn, ngrams')
    parser.add_argument('-all', action='store_true', help='meta, pdf, txt, inner_vector, knn, ngrams')
    parser.add_argument('-retrain', action='store_true', help='Do we need to retrain recommendation model?')
    parser.add_argument('-update_categories', action='store_true', help='Move categories description from GLOBAL to DB')

    parser.add_argument('-download_meta', action='store_true', help='Do we need to download articles from arXiv?')
    parser.add_argument('-download_pdf', action='store_true', help='Do we need to download pdf?')
    parser.add_argument('-pdf2txt', action='store_true', help='Do we need to generate TXT?')
    parser.add_argument('-inner_vector', action='store_true', help='Do we need to calculate inner vectors?')
    parser.add_argument('-knn', action='store_true', help='Do we need to calculate nearest articles?')
    parser.add_argument('-category_bar', action='store_true', help='Do we need to count articles in category bar?')
    parser.add_argument('-ngrams', action='store_true', help='Do we need to update Ngrams Trend lines?')

    parser.add_argument('--batch_size', type=int, help='Articles per iteration', default=100)
    parser.add_argument('--max_articles', type=int, help='number of data loading workers', default=200)
    parser.add_argument('--sleep_time', type=int, help='How much time of sleep (in sec) between API calls', default=5)

    args = parser.parse_args()
    return args


def overall_stats():
    articles = Article.objects
    logger.info('DATABASE stats:')
    logger.info('\tNumber of articles:                          %d' % articles.count())
    logger.info('\tNumber of articles with pdf:                 %d' % articles.filter(has_pdf=True).count())
    logger.info('\tNumber of articles with txt:                 %d' % articles.filter(has_txt=True).count())
    logger.info('\tNumber of articles with inner vector:        %d' % articles.filter(has_inner_vector=True).count())
    logger.info('\tNumber of articles with neighbors:           %d' % articles.filter(has_neighbors=True).count())
    logger.info('\tNumber of articles with counted category:    %d' % articles.filter(has_category_bar=True).count())
    logger.info('\tNumber of articles with ngram stats:         %d' % articles.filter(has_ngram_stat=True).count())


def _get_max_articles(articles, max_articles):
    upper_bound = articles.count()
    if upper_bound == 0:
        logger.info('All articles are up to date!')
        return 0

    if max_articles <= 0 or max_articles >= upper_bound:
        logger.info('There are %d articles. Take all' % upper_bound)
        return upper_bound

    logger.info('There are %d articles. Take only %d of them' % (upper_bound, max_articles))
    return max_articles


@log.logging.timeit(logger, 'Download Meta Time', level=logging.INFO)
def download_meta(args):
    logger.info('START downloading metas from arXiv')
    arxiv_api = ArXivAPI(args.sleep_time)
    db = DBManager()

    attempt = 1
    start = 0
    ok_list = []
    pbar = tqdm.tqdm(total=args.max_articles, desc='Total articles')

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


@log.logging.timeit(logger, 'Download PDF Time', level=logging.INFO)
def download_pdf(args, path_pdf='data/pdfs'):
    logger.info('START downloading PDFs from arXiv')

    articles = Article.objects.filter(has_pdf=False)
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('FINISH downloading PDFs from arXiv')
        return

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


@log.logging.timeit(logger, 'PDF 2 TXT Time', level=logging.INFO)
def pdf2txt(args, path_pdf='data/pdfs', path_txt='data/txts'):
    logger.info('START generating TXTs from PDFs')
    db = DBManager()

    articles = Article.objects.filter(Q(has_pdf=True) & Q(has_txt=False))
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('FINISH generating TXTs from PDFs')
        return

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

        try:
            with open(file_txt, 'r', encoding='unicode_escape') as f:
                text = ' '.join(f.readlines())[:100000]
        except Exception as e:
            logger.debug(idx + '. Decode problem. No .txt file (Next): ' + str(e))
            continue

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


@log.logging.timeit(logger, 'Retraining model Time', level=logging.INFO)
def retrain(args):
    logger.info('START Retraining model')

    articles = Article.objects.filter(has_txt=True)
    max_articles = _get_max_articles(articles, args.max_articles)

    model = RelationModel()
    model.retrain(logger, train_size=max_articles)

    logger.info('Training is finished. Set all flags to False')
    ArticleVector.objects.all().delete()
    Article.objects.update(has_inner_vector=False)
    ArticleArticleRelation.objects.all().delete()
    Article.objects.update(has_neighbors=False)
    logger.info('FINISH Retraining model')


@log.logging.timeit(logger, 'Calculate Inner Vector Time', level=logging.INFO)
def calc_inner_vector(args):
    logger.info('START making relations')
    db = DBManager()
    model = RelationModel()

    if model.trained is False:
        logger.info("Relation model not trained. Let's train first (-retrain).")
        return

    articles = Article.objects.filter(Q(has_txt=True) & Q(has_inner_vector=False))
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('FINISH making relations')
        return

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


@log.logging.timeit(logger, 'Calculate nearest articles', level=logging.INFO)
def calc_nearest_articles(args, n_nearest=20):
    logger.info('START calculating nearest articles')
    db = DBManager()
    model = RelationModel()

    if model.trained is False:
        logger.info("Relation model not trained. Let's train first (-retrain).")
        logger.info('FINISH calculating nearest articles')
        return

    db_articles = Article.objects.filter(has_neighbors=True)
    new_articles = Article.objects.filter(Q(has_inner_vector=True) & Q(has_neighbors=False))

    max_articles = _get_max_articles(new_articles, args.max_articles)

    if max_articles == 0:
        logger.info('No articles for calculating (has_inner_vector=True & has_neighbors=False)')
        logger.info('FINISH calculating nearest articles')
        return
    elif db_articles.count() < n_nearest + 1 and  max_articles < n_nearest + 1:
        error_str = 'need batch_size > {}. Now batch_size = {}'.format(n_nearest, max_articles)
        logger.info('For proper calculations we ' + error_str)
        logger.info('FINISH calculating nearest articles')
        return

    logger.info('READ {} new articles and {} old articles from db'.format(max_articles, db_articles.count()))
    articles = new_articles.values('id', 'articlevector__inner_vector')[:max_articles]
    articles = pd.DataFrame(articles)
    ids = articles.id.values
    features = np.vstack(articles.articlevector__inner_vector.apply(np.frombuffer))

    border = len(articles)

    if db_articles.count() != 0:
        df = pd.DataFrame(db_articles.values('id', 'articlevector__inner_vector'))
        ids = np.concatenate((ids, df['id'].values))
        features = np.concatenate((features, np.vstack(df.articlevector__inner_vector.apply(np.frombuffer))))

    logger.info('FIT knn on {} articles'.format(len(features)))
    knn = NearestNeighbors()
    knn.fit(features)
    dists, nn = knn.kneighbors(features, n_nearest+1)

    logger.info('Process {} articles'.format(len(features)))
    count = -border
    for dist, ns in tqdm.tqdm(zip(dists, nn), total=len(features)):
        if sum(ns < border) == 0:
            continue
        count += 1
        ArticleArticleRelation.objects.filter(left_id=ids[ns[0]]).all().delete()
        items = [ArticleArticleRelation(
            left_id=ids[ns[0]],
            right_id=ids[n],
            distance=d
        ) for d, n in zip(dist[1:], ns[1:])]
        db.bulk_create(items)
        Article.objects.filter(pk=ids[ns[0]]).update(has_neighbors=True)
    logger.info('Created {} new articles and updated {} old articles'.format(border, count))

    num_labeled = Article.objects.filter(has_neighbors=True).count()
    num_items = ArticleArticleRelation.objects.count()
    if num_items == num_labeled * n_nearest:
        logger.info('OK. Total {} articles with {} nn rows in DB'.format(num_labeled, num_items))
    else:
        logger.warning('!!! Total {} articles with {} nn rows in DB'.format(num_labeled, num_items))
    logger.info('FINISH calculating nearest articles')


@log.logging.timeit(logger, 'Update categories Time', level=logging.INFO)
def update_categories_name():
    logger.info('START Updating categories')
    ok, not_ok = 0, 0
    for cat in Categories.objects.all():
        if cat.category in GLOBAL__CATEGORIES:
            cat.category_full = GLOBAL__CATEGORIES[cat.category]
            cat.save()
            ok += 1
            logger.info('UPDATE ' + cat.category + ': ' + GLOBAL__CATEGORIES[cat.category])
        else:
            logger.warning('NOT SPECIFIED ' + cat.category)
            not_ok += 1
    logger.info('FINISH Updating categories (%d updated and %d not specified)' % (ok, not_ok))


@log.logging.timeit(logger, 'Stacked Bar Time', level=logging.INFO)
def stacked_bar(args):
    logger.info('START Stacked bar')
    db = DBManager()

    articles = Article.objects.filter(has_category_bar=False)
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('No articles for count categories')
        logger.info('FINISH Stacked bar')
        return

    articles = articles.values('id', 'date', 'category')[:max_articles]
    articles = pd.DataFrame(articles)
    articles['date'] = pd.to_datetime(articles['date'])

    next_month = datetime.datetime.now() + relativedelta(months=1)
    min_date_code_in_db = CategoriesDate.objects.order_by('date').first()
    if min_date_code_in_db is None:
        min_date_code_in_db = next_month.month + next_month.year * 100
        logger.debug('No dates in DB. Select min date: %d' % min_date_code_in_db)
    else:
        min_date_code_in_db = min_date_code_in_db.date_code
        logger.debug('Min date in DB: %d' % min_date_code_in_db)

    min_date = articles.date.min()
    min_date_code = min_date.month + min_date.year * 100

    if min_date_code >= min_date_code_in_db:
        logger.info('All months are present')
    else:
        logger.info('Append new months from %d to %d' % (min_date_code, min_date_code_in_db))
        date_code = min_date_code
        while date_code != min_date_code_in_db:
            date = datetime.date(year=date_code // 100, month=date_code % 100, day=1)
            new_date, _ = CategoriesDate.objects.update_or_create(date_code=date_code, date=date.strftime('%b %y'))
            new_date.save()

            if Categories.objects.count() != 0:
                db.bulk_create([CategoriesVSDate(
                    category=c,
                    from_month=new_date,
                    count=0
                ) for c in Categories.objects.all()])

            if date_code % 100 == 12:
                date_code = date_code - 11 + 100
            else:
                date_code += 1

    new_categories = articles.category.unique()
    old_categories = list(Categories.objects.values_list('category', flat=True))

    append_categories = new_categories[~np.in1d(new_categories, old_categories)]
    if len(append_categories) == 0:
        logger.info('All categories are present')
    else:
        logger.warning('Categories does not exists: ' + ', '.join(append_categories))
        logger.warning('!!! You need to manually specify this category in DB')
        logger.warning('!!! And append this category to utils.constants.GLOBAL__CATEGORIES')

        for cat in append_categories:
            new_category, _ = Categories.objects.update_or_create(category=cat, category_full='NOT SPECIFIED')
            new_category.save()

            db.bulk_create([CategoriesVSDate(
                from_category=new_category,
                from_month=d,
                count=0
            ) for d in CategoriesDate.objects.all()])

    logging.info('Update bar counts')
    for _, row in tqdm.tqdm(articles.iterrows(), total=len(articles)):
        date_code = row['date'].month + row['date'].year * 100
        CategoriesVSDate.objects.filter(
            from_category__category=row['category'],
            from_month__date_code=date_code
        ).update(count=F('count') + 1)

        Article.objects.filter(id=row['id']).update(has_category_bar=True)

    logger.info('FINISH Stacked bar')


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


@log.logging.timeit(logger, 'Ngram Trend Line Time', level=logging.INFO)
def trend_ngrams(args, max_n_for_grams=3):
    logger.info('START Ngram Trend Line')
    db = DBManager()

    articles = Article.objects.filter(Q(has_txt=True) & Q(has_ngram_stat=False))
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('No articles for ngrams')
        logger.info('FINISH Ngram Trend Line')
        return

    articles = articles.values('id', 'date', 'title', 'abstract', 'articletext__text')[:max_articles]
    articles = pd.DataFrame(articles)
    articles['date'] = pd.to_datetime(articles['date'])
    articles['idx_sort'] = articles.date.dt.month + articles.date.dt.year * 100

    for _, row in tqdm.tqdm(articles.iterrows(), total=len(articles), desc='Total'):
        date_code = row['idx_sort']

        if NGramsMonth.objects.filter(label_code=date_code).count() == 0:
            label = datetime.date(date_code//100, date_code%100, 1).strftime('%b %y')
            db.bulk_create([NGramsMonth(
                label_code=date_code,
                label=label,
                length=i+1
            ) for i in range(max_n_for_grams)])

        dics_ttl, keys_ttl = get_grams_dict([row['title']], max_n_for_grams)
        dics_abs, keys_abs = get_grams_dict([row['abstract']], max_n_for_grams)
        dics_txt, keys_txt = get_grams_dict([row['articletext__text']], max_n_for_grams)

        keys = list(set(np.concatenate((keys_ttl, keys_abs, keys_txt))))
        existed_keys = list(NGramsSentence.objects.filter(sentence__in=keys).values_list(flat=True))
        new_keys = np.array(keys)[~np.in1d(keys, existed_keys)]

        db.bulk_create([NGramsSentence(sentence=k) for k in new_keys])
        months = NGramsMonth.objects.filter(label_code=date_code).order_by('length')
        db.bulk_create([SentenceVSMonth(
            from_corpora=months[len(key.split()) - 1],
            from_item=NGramsSentence.objects.filter(sentence=key)[0],
            freq_title=dics_ttl[len(key.split()) - 1].get(key, 0),
            freq_abstract=dics_abs[len(key.split()) - 1].get(key, 0),
            freq_text=dics_txt[len(key.split()) - 1].get(key, 0)
        ) for key in tqdm.tqdm(new_keys, desc='New sentences in %d' % date_code)])

        for key in tqdm.tqdm(existed_keys, 'Update sentences in %d' % date_code):
            idx_len = len(key.split()) - 1
            target = SentenceVSMonth.objects.filter(
                from_corpora=months[idx_len],
                from_item=NGramsSentence.objects.filter(sentence=key)[0]
            )
            if len(target) == 0:
                SentenceVSMonth.objects.update_or_create(
                    from_corpora=months[idx_len],
                    from_item=NGramsSentence.objects.filter(sentence=key)[0],
                    freq_title=dics_ttl[idx_len].get(key, 0),
                    freq_abstract=dics_abs[idx_len].get(key, 0),
                    freq_text=dics_txt[idx_len].get(key, 0),
                )
            else:
                target.update(
                    freq_title=F('freq_title') + dics_ttl[idx_len].get(key, 0),
                    freq_abstract=F('freq_abstract') + dics_abs[idx_len].get(key, 0),
                    freq_text=F('freq_text') + dics_txt[idx_len].get(key, 0),
                )

        Article.objects.filter(pk=row['id']).update(has_ngram_stat=True)


@log.logging.timeit(logger, 'Total Time', level=logging.INFO)
def main(args):
    path, path_pdf, path_txt = 'data', 'data/pdfs', 'data/txts'
    for d in [path, path_pdf, path_txt]:
        if not os.path.exists(d):
            os.mkdir(d)

    overall_stats()

    if args.update_categories:
        update_categories_name()

    if args.download_meta or args.all:
        download_meta(args)

    if args.download_pdf or args.all or args.clean:
        download_pdf(args, path_pdf)

    if args.pdf2txt or args.all or args.clean:
        pdf2txt(args, path_pdf, path_txt)

    if args.retrain:
        retrain(args)

    if args.inner_vector or args.all or args.clean:
        calc_inner_vector(args)

    if args.knn or args.all or args.clean:
        calc_nearest_articles(args)

    if args.category_bar or args.all or args.clean:
        stacked_bar(args)

    if args.ngrams or args.all or args.clean:
        trend_ngrams(args)

    logger.debug('#'*50)
    overall_stats()
    logger.debug('#'*50)


if __name__ == '__main__':
    args = parse_args()
    main(args)

