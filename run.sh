#!/usr/bin/env bash
rm -rf db.sqlite3
rm -rf articles/migrations
python manage.py makemigrations
python manage.py makemigrations articles
python manage.py migrate
python scripts/increment.py

python manage.py createsuperuser