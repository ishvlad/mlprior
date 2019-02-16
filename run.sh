#!/usr/bin/env bash
rm -rf db.sqlite3
rm -rf articles/migrations
python manage.py makemigrations
python manage.py makemigrations articles
python scripts/arxiv_retreive.py
python manage.py migrate
python scripts/relation_store.py
python scripts/visualization_store.py

python manage.py createsuperuser