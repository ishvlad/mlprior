# mlprior

Requirements:

```bash
pip install -r requirements.txt
```

DB migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Django server

```bash
python manage.py runserver
```

Arxiv retrieve:

```bash
python scripts/arxiv_retreive.py
```


Elastic Search setup and run

```bash
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.6.1.tar.gz
tar -xzf elasticsearch-6.6.1.tar.gz

./elasticsearch-6.6.1/bin/elasticsearch
```

