import argparse
import datetime
import json
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

from articles.api import TrendAPI, CategoriesAPI
from articles.models import Article, Categories, NGramsMonth, ArticleText, DefaultStore
from collections import Counter
from services.arxiv import ArXivArticle, ArXivAPI
from django.db.models import F, Q
from nltk import ngrams
from services.github.helpers import send_github_url_to_server, find_github_repo_in_text
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
    parser.add_argument('-update_default', action='store_true', help='Update default dics for visualization')

    parser.add_argument('-download_meta', action='store_true', help='Do we need to download articles from arXiv?')
    parser.add_argument('-download_pdf', action='store_true', help='Do we need to download pdf?')
    parser.add_argument('-pdf2txt', action='store_true', help='Do we need to generate TXT?')
    parser.add_argument('-inner_vector', action='store_true', help='Do we need to calculate inner vectors?')
    parser.add_argument('-knn', action='store_true', help='Do we need to calculate nearest articles?')
    parser.add_argument('-category_bar', action='store_true', help='Do we need to count articles in category bar?')
    parser.add_argument('-ngrams', action='store_true', help='Do we need to update Ngrams Trend lines?')

    parser.add_argument('--batch_size', type=int, help='Articles per iteration', default=200)
    parser.add_argument('--max_articles', type=int, help='number of data loading workers', default=200)
    parser.add_argument('--sleep_time', type=int, help='How much time of sleep (in sec) between API calls', default=6)
    parser.add_argument('--verbose', type=bool, help='Do we need to print all?', default=True)

    args = parser.parse_args()
    return args


def overall_stats():
    articles = Article.objects

    txt_batch = articles.filter(has_txt=True).count(), articles.filter(has_txt=None).count()
    txt_batch = txt_batch[0]+txt_batch[1], txt_batch[0], txt_batch[1]
    logger.info('DATABASE stats:')
    logger.info('\tNumber of articles:                          %d' % articles.count())
    logger.info('\tNumber of articles with pdf:                 %d' % articles.filter(has_pdf=True).count())
    logger.info('\tNumber of articles with txt:                 %d (%d OK, %d null)' % txt_batch)
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

    proba_for_random = 0.2
    attempt = 1
    start = 0
    ok_list = []
    pbar = tqdm.tqdm(total=args.max_articles, desc='Total articles')

    while len(ok_list) < args.max_articles:
        logger.info('BUFFER is empty. arXiv.API -- Try to get %d articles...' % args.batch_size)

        random_search = np.random.rand() < proba_for_random
        if random_search:
            start_random = np.random.randint(2 * Article.objects.count())
        else:
            start_random = start

        entries = arxiv_api.search(
            categories=['cat:' + c for c in GLOBAL__CATEGORIES if c.startswith('cs.')],
            start=start_random, max_result=args.batch_size,
            is_random=random_search
        )
        logger.info('... received %d articles from arXiv start from %d index' % (len(entries), start_random))

        if not random_search:
            start += args.batch_size

        if len(entries) == 0:
            if not random_search:
                start -= args.batch_size
            if attempt < 10:
                logger.info('Empty buffer again. ArXiv is over :) Attempt %d.' % attempt)
                attempt += 1
            else:
                logger.info('Empty buffer again. ArXiv is over :) Stop downloading.')
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
            logger.info('There are %d new articles. Append to list' % len(entries))
            ok_list += entries
            arr = entries
            if args.verbose:
                arr = tqdm.tqdm(entries)
            for a in arr:
                db.add_article(a)
            pbar.update(len(entries))
        else:
            logger.info('arXiv.API: no new articles')

    pbar.close()
    logger.info('FINISH downloading %d metas from arXiv' % len(ok_list))


@log.logging.timeit(logger, 'Download PDF Time', level=logging.INFO)
def download_pdf(args, path_pdf='data/pdfs', path_txt='data/txts'):
    logger.info('START downloading PDFs from arXiv')

    articles = Article.objects.filter(has_pdf=False).order_by('-date')
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('FINISH downloading PDFs from arXiv')
        return


    pbar = tqdm.tqdm(total=max_articles)
    ok_list = []
    # null_list = []
    for pk, idx, url in articles.values_list('pk', 'arxiv_id', 'url'):
        if len(ok_list) >= max_articles:
            break

        file_pdf = os.path.join(path_pdf, str(idx) + '.pdf')
        file_txt = os.path.join(path_txt, str(idx) + '.txt')
        url += '.pdf'

        if os.path.exists(file_pdf) and os.path.getsize(file_pdf) != 0:
            logger.info('PDF ' + idx + ' already exists. Just update flag')
            ok_list.append(pk)
            pbar.update(1)
            continue

        if os.path.exists(file_txt) and os.path.getsize(file_txt) != 0:
            logger.info('PDF ' + idx + ' does not exist but TXT already exists. Just update flag')
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
            logger.info(str(idx) + ' (' + str(url) + '): Cannot download PDF. Exception: ' + str(e))
            # null_list.append(pk)

    pbar.close()
    logger.info('FINISH downloading PDFs from arXiv. Now update flags of %d articles' % len(ok_list))
    if len(ok_list) != 0:
        Article.objects.filter(pk__in=ok_list).update(has_pdf=True)
    # if len(null_list) != 0:
    #     Article.objects.filter(pk__in=null_list).update(has_pdf=None)


@log.logging.timeit(logger, 'PDF 2 TXT Time', level=logging.INFO)
def pdf2txt(args, path_pdf='data/pdfs', path_txt='data/txts'):
    logger.info('START generating TXTs from PDFs')
    db = DBManager()

    articles = Article.objects.filter(Q(has_pdf=True) & Q(has_txt=False)).order_by('-date')
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('FINISH generating TXTs from PDFs')
        return

    pbar = tqdm.tqdm(total=max_articles)
    ok_list, null_list = [], []
    idx_list = []
    new_items = []

    for pk, idx in articles.values_list('pk', 'arxiv_id'):
        if len(ok_list) >= max_articles:
            break

        file_pdf = os.path.join(path_pdf, idx + '.pdf')
        file_txt = os.path.join(path_txt, idx + '.txt')

        if os.path.exists(file_txt) and os.path.getsize(file_txt) != 0:
            arts = ArticleText.objects.filter(article_origin=pk).values('text')

            if len(arts) != 0 and arts[0]['text'] is not None:
                logger.info('TXT ' + idx + ' already exists. Just update flag')

                # GIT
                git = find_github_repo_in_text(arts[0]['text'])
                if git is not None:
                    res = send_github_url_to_server(git, idx)
                    logger.info('Find gitHub link of ' + idx + ': ' + str(git) +
                                '. Result: ' + str(res.status_code) + ': ' + str(res.text))

                    if res.status_code == 500 or res.status_code == 504:
                        logger.info('NO save ' + str(idx) + ' because of GIT. Try again latetr')
                        continue
                else:
                    logger.info('NO GIT on ' + str(idx))

                ok_list.append(pk)
                idx_list.append(idx)
                pbar.update(1)

            else:
                logger.info('TXT ' + idx + ' already exists, but text not appears in DB. Save text')
        else:
            cmd = "pdftotext %s %s " % (file_pdf, file_txt)
            os.system(cmd)

            if not os.path.isfile(file_txt) or os.path.getsize(file_txt) == 0:
                logger.info(idx + '. pdf2txt: Failed to generate TXT (No .txt file)). NEXT')

        try:
            with open(file_txt, 'r', encoding='unicode_escape') as f:
                text = ' '.join(f.readlines())[:100000]
                if '\x00' in text:
                    text = text.replace('\x00', ' ')
                text = text.encode('utf-8', 'replace').decode('utf-8')

        except Exception as e:
            logger.info(idx + '. Decode problem. No .txt file. NEXT: ' + str(e))
            text = 'NO TEXT'
            null_list.append(pk)

        new_items.append(ArticleText(
            article_origin_id=pk,
            pdf_location=file_pdf,
            txt_location=file_txt,
            text=text
        ))

        # GIT
        git = find_github_repo_in_text(text)
        if git is not None:
            res = send_github_url_to_server(git, idx)
            logger.info('Find gitHub link of ' + idx + ': ' + str(git) +
                        '. Result: ' + str(res.status_code) + ': ' + str(res.text))

            if res.status_code == 500 or res.status_code == 504:
                logger.info('NO save ' + str(idx) + ' because of GIT. Try again later')
                continue
        else:
            logger.info('NO GIT on ' + str(idx))

        ok_list.append(pk)
        idx_list.append(idx)
        pbar.update(1)

    pbar.close()
    logger.info('FINISH generating TXTs. Now update flags of %d articles' % len(ok_list))
    if len(ok_list) != 0:
        db.bulk_create(new_items)
        Article.objects.filter(pk__in=ok_list).update(has_txt=True)
    if len(null_list) != 0:
        Article.objects.filter(pk__in=null_list).update(has_txt=None)
    for idx in idx_list:
        f = os.path.join(path_pdf, idx + '.pdf')
        if os.path.exists(f):
            cmd = "rm -rf %s" % f
            os.system(cmd)


@log.logging.timeit(logger, 'Calculate Inner Vector Time', level=logging.INFO)
def calc_inner_vector(args):
    logger.info('START making relations')
    model = RelationModel()

    if model.trained is False:
        logger.info("Relation model not trained. Let's train first (-retrain).")
        return

    articles = Article.objects.filter(Q(has_txt=True) & Q(has_inner_vector=False)).order_by('-date')
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('FINISH making relations')
        return

    cols = ['id', 'title', 'abstract', 'articletext__text']
    articles = articles.values(*cols)[:max_articles]
    articles = pd.DataFrame(articles)

    for id, ttl, abs, txt in tqdm.tqdm(articles[cols].values, desc='Tags generation'):
        tags = model.get_tags(ttl, abs, txt)
        item = ArticleText.objects.filter(article_origin_id=id)
        if len(item) != 1:
            logging.warning('No ArticleText instance for id={} (but has_txt=True)'.format(id))
        item = item[0]
        item.tags = dict([(t[0], str(t[1])) for t in tags.items()])
        item.tags_norm = sum(tags.values())
        item.save()
        Article.objects.filter(pk=id).update(has_inner_vector=True)

    logger.info('FINISH making relations')


@log.logging.timeit(logger, 'Calculate nearest articles', level=logging.INFO)
def calc_nearest_articles(args):
    logger.info('START calculating nearest articles')
    model = RelationModel()

    if model.trained is False:
        logger.info("Relation model not trained. Let's train first (-retrain).")
        logger.info('FINISH calculating nearest articles')
        return

    db_articles = Article.objects.filter(has_neighbors=True)
    new_articles = Article.objects.filter(Q(has_inner_vector=True) & Q(has_neighbors=False)).order_by('-date')

    max_articles = _get_max_articles(new_articles, args.max_articles)

    if max_articles == 0:
        logger.info('No articles for calculating (has_inner_vector=True & has_neighbors=False)')
        logger.info('FINISH calculating nearest articles')
        return

    logger.info('READ {} new articles and {} old articles from db'.format(max_articles, db_articles.count()))

    cols = ['id', 'articletext__tags', 'articletext__tags_norm']
    articles = new_articles.values(*cols)[:max_articles]
    articles = pd.DataFrame(articles)

    for id, source_tags, source_norm in tqdm.tqdm(articles[cols].values, desc='Calc distances'):
        db_articles = Article.objects.filter(has_neighbors=True)
        if db_articles.count() == 0:
            Article.objects.filter(id=id).update(has_neighbors=True)
            continue

        source_relations = {}
        targets = db_articles.values('id', 'articletext__tags', 'articletext__tags_norm', 'articletext__relations')

        for target in tqdm.tqdm(targets, desc='All articles in DB'):
            dist = model.get_dist(source_tags, target['articletext__tags'],
                                  source_norm, target['articletext__tags_norm'])

            need_update, new_dict = model.update_dict(source_relations, str(target['id']), str(dist))
            if need_update:
                source_relations = new_dict

            need_update, new_dict = model.update_dict(target['articletext__relations'], str(id), str(dist))
            if need_update:
                target['articletext__relations'] = new_dict
                ArticleText.objects.filter(article_origin_id=target['id']).update(
                    relations=target['articletext__relations']
                )

        ArticleText.objects.filter(article_origin_id=id).update(relations=source_relations)
        Article.objects.filter(id=id).update(has_neighbors=True)

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

    articles = Article.objects.filter(has_category_bar=False).order_by('-date')
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('No articles for count categories')
        logger.info('FINISH Stacked bar')
        return

    articles = articles.values('id', 'date', 'category')[:max_articles]
    articles = pd.DataFrame(articles)
    articles['date'] = pd.to_datetime(articles['date'])

    logging.info('Update bar counts')
    for _, row in tqdm.tqdm(articles.iterrows(), total=len(articles)):
        date_code = str(row['date'].month + row['date'].year * 100)

        # new category
        db_item = Categories.objects.filter(category=row['category'])
        if db_item.count() == 0:
            logger.warning('Category does not exists: ' + row['category'])
            logger.warning('!!! And append this category to utils.constants.GLOBAL__CATEGORIES')

            Categories(
                category=row['category'],
                months={date_code: '1'}
            ).save()
        else:
            db_item = db_item[0]
            if date_code in db_item.months:
                db_item.months[date_code] = str(int(db_item.months[date_code]) + 1)
            else:
                db_item.months[date_code] = '1'
            db_item.save()

        Article.objects.filter(id=row['id']).update(has_category_bar=True)

    logger.info('FINISH Stacked bar')


def get_grams_dict(sentences, max_ngram_len=5):
    p = re.compile('\w+[\-\w+]*', re.IGNORECASE)
    dic = {}

    for n in range(1, max_ngram_len + 1):
        for s in sentences:
            grams = ngrams(p.findall(s.lower()), n)

            for key in set(grams):
                key = ' '.join(key)
                if len(key) < 250:
                    if key in dic:
                        dic[key] += 1
                    else:
                        dic[key] = 1

    return dic


@log.logging.timeit(logger, 'Ngram Trend Line Time', level=logging.INFO)
def trend_ngrams(args, max_n_for_grams=3):
    logger.info('START Ngram Trend Line')
    db = DBManager()

    articles = Article.objects.filter(Q(has_txt=True) & Q(has_ngram_stat=False)).order_by('-date')
    max_articles = _get_max_articles(articles, args.max_articles)

    if max_articles == 0:
        logger.info('No articles for ngrams')
        logger.info('FINISH Ngram Trend Line')
        return

    articles = articles.values('id', 'date', 'title', 'abstract')[:max_articles]
    articles = pd.DataFrame(articles)
    articles['date'] = pd.to_datetime(articles['date'])
    articles['idx_sort'] = articles.date.dt.month + articles.date.dt.year * 100
    df_group = articles.groupby('idx_sort')

    for date_code, row in tqdm.tqdm(df_group, total=len(df_group), desc='Total'):
        if NGramsMonth.objects.filter(label_code=date_code).count() == 0:
            label = datetime.date(date_code // 100, date_code % 100, 1).strftime('%b %y')
            db.bulk_create([NGramsMonth(
                label_code=date_code,
                label=label,
                type=i
            ) for i in range(3)])  # 3 = title, abstract, text

        dics_ttl = get_grams_dict(list(row.title.values), max_n_for_grams)
        dics_abs = get_grams_dict(list(row.abstract.values), max_n_for_grams)

        db_ttl = NGramsMonth.objects.filter(label_code=date_code, type=0)[0]
        s = Counter({k: int(v) for (k, v) in db_ttl.sentences.items()})
        db_ttl.sentences = dict(Counter(s) + Counter(dics_ttl))
        db_ttl.save()

        db_abs = NGramsMonth.objects.filter(label_code=date_code, type=1)[0]
        s = Counter({k: int(v) for (k, v) in db_abs.sentences.items()})
        db_abs.sentences = dict(Counter(s) + Counter(dics_abs))
        db_abs.save()

        pks = list(row['id'].values)
        Article.objects.filter(pk__in=pks).update(has_ngram_stat=True)


@log.logging.timeit(logger, 'Default update Time', level=logging.INFO)
def update_default(args):
    # logger.info('Updating Trend default data')
    # response = TrendAPI().get(None, 'Supervised, Unsupervised, Reinforcement')
    #
    # if response.status_code != 200:
    #     logger.warning('ERROR while receiving trends data. Skip')
    # else:
    #     item, _ = DefaultStore.objects.get_or_create(key='trends')
    #     data = json.dumps(response.data)
    #     item.value = data
    #     item.save()
    #     logger.info('OK Updating Trend default data (len = %d)' % len(data))

    logger.info('Updating Categories default data')
    response = CategoriesAPI().get(None, 'cs.AI, cs.CV, cs.DS, cs.SI')

    if response.status_code != 200:
        logger.warning('ERROR while receiving categories data. Skip')
    else:
        item, _ = DefaultStore.objects.get_or_create(key='categories')
        data = json.dumps(response.data)
        item.value = data
        item.save()
        logger.info('OK Updating Categories default data (len = %d)' % len(data))


@log.logging.timeit(logger, 'Total Time', level=logging.INFO)
def main(args):
    path, path_pdf, path_txt = 'data', 'data/pdfs', 'data/txts'
    for d in [path, path_pdf, path_txt]:
        if not os.path.exists(d):
            os.mkdir(d)

    overall_stats()

    if args.update_categories or args.clean:
        update_categories_name()

    if args.download_meta or args.all:
        download_meta(args)

    if args.download_pdf or args.all or args.clean:
        download_pdf(args, path_pdf)

    if args.pdf2txt or args.all or args.clean:
        pdf2txt(args, path_pdf, path_txt)

    if args.retrain:
        raise NotImplementedError()

    if args.inner_vector or args.all or args.clean:
        calc_inner_vector(args)

    if args.knn or args.all or args.clean:
        calc_nearest_articles(args)

    if args.category_bar or args.all or args.clean:
        stacked_bar(args)

    if args.ngrams or args.all or args.clean:
        trend_ngrams(args)

    if args.update_default or args.all or args.clean:
        update_default(args)

    logger.info('#'*50)
    overall_stats()
    logger.info('#'*50)


if __name__ == '__main__':
    args = parse_args()
    main(args)

