#!/usr/bin/env bash
rm -rf db.sqlite3
python manage.py makemigrations
python manage.py makemigrations articles
python manage.py migrate
python scripts/arxiv_retreive.py
python scripts/relation_filling.py
python manage.py runserver