#!/usr/bin/env bash
rm -rf db.sqlite3
rm -rf articles/migrations core/migrations
python manage.py makemigrations
python manage.py makemigrations articles
python manage.py makemigrations core
python manage.py migrate
#python scripts/increment.py --max_articles 50

# python manage.py createsuperuser