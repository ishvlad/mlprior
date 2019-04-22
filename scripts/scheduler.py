import argparse
import datetime
import json
import numpy
import os
import sys

from pickle import load, dump
from uuid import uuid4


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--border', type=int, help='Difference for start', default=10)
    parser.add_argument('--max_articles', type=int, help='Difference for start', default=100)
    parser.add_argument('--path', type=str, default='/home/mlprior/git_app/')
    parser.add_argument('--python', type=str, default='/home/mlprior/anaconda3/envs/py37/bin/python ')

    args = parser.parse_args()
    return args


def main(args):
    path = args.path
    queue_path = os.path.join(path, 'scripts/queue.json')
    script_path = os.path.join(path, 'scripts/increment.py')
    logs_path = os.path.join(path, 'data/logs/scheduler/')
    key = str(uuid4())
    task = ''
    border = args.border

    if not os.path.exists(logs_path):
        os.mkdir(logs_path)

    sys.path.append(path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mlprior.settings")

    import django

    django.setup()

    from articles.models import Article

    try:
        articles = Article.objects
        total_count = articles.count()

        has_pdf = articles.filter(has_pdf=True).count()
        has_txt = articles.filter(has_txt=True).count()
        has_inner_vector = articles.filter(has_inner_vector=True).count()
        has_nn = articles.filter(has_neighbors=True).count()
        has_categories = articles.filter(has_category_bar=True).count()
        has_ngrams_stat = articles.filter(has_ngram_stat=True).count()

        if os.path.exists(queue_path):
            with open(queue_path, 'r') as json_file:
                queue = json.load(json_file)
        else:
            queue = {}

        coin = numpy.random.randint(7)

        if coin == 0 and 'ngrams' not in queue and (has_txt - has_ngrams_stat > border):
            task = 'ngrams'
        elif coin == 1 and 'category_bar' not in queue and (total_count - has_categories > border):
            task = 'update_categories -category_bar'
        elif coin == 2 and 'knn' not in queue and (has_inner_vector - has_nn > border):
            task = 'knn'
        elif coin == 3 and 'inner_vector' not in queue and (has_txt - has_inner_vector > border):
            task = 'inner_vector'
        elif coin == 4 and 'pdf2txt' not in queue and (has_pdf - has_txt > border):
            task = 'pdf2txt'
        elif coin == 5 and 'download_pdf' not in queue and (total_count - has_pdf > border):
            task = 'download_pdf'
        elif coin == 6 and 'download_meta' not in queue:
            task = 'download_meta'

        if task != '':
            queue[task] = key
            with open(queue_path, 'w+') as outfile:
                json.dump(queue, outfile)
            time = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
            cmd = args.python + ' ' + script_path
            cmd += (" -%s --max_articles=%s --verbose=False " % (task, args.max_articles))
            cmd += "2> " + os.path.join(logs_path, "scheduler_%s_%s.err " % (time, task))
            os.system(cmd)

    except Exception as e:
        with open(os.path.join(logs_path, 'scheduler.err'), 'w+') as f:
            string = datetime.datetime.now().strftime('%Y-%m-%d-%H.%M.%S')
            string += ' ' + task + ': ' + str(e) + '\n'
            f.write(string)
    finally:
        if task != '':
            with open(queue_path, 'r') as json_file:
                queue = json.load(json_file)
            if task in queue and queue[task] == key:
                del queue[task]
                with open(queue_path, 'w+') as outfile:
                    json.dump(queue, outfile)


if __name__ == '__main__':
    args = parse_args()
    main(args)
