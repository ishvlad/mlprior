#!/usr/bin/env bash

sudo apt-get install supervisor
sudo cp /home/mlprior/git_app/config_files/supervisor/mlprior_celery.conf /etc/supervisor/conf.d/
sudo cp /home/mlprior/git_app/config_files/supervisor/mlprior_celerybeat.conf /etc/supervisor/conf.d/

sudo mkdir /var/log/celery
sudo touch /var/log/celery/mlprior_worker.log
sudo touch /var/log/celery/mlprior_beat.log

sudo supervisorctl reread
sudo supervisorctl update

sudo supervisorctl start mlpcelery
sudo supervisorctl status mlpcelery