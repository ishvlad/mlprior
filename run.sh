#!/usr/bin/env bash
rm -rf db.sqlite3
rm -rf articles/migrations core/migrations log/migrations
python manage.py makemigrations
python manage.py makemigrations articles
python manage.py makemigrations core
python manage.py makemigrations log
python manage.py migrate
python scripts/increment.py --max_articles 100 -all
python manage.py search_index --rebuild


# python manage.py createsuperuser