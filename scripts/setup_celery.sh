#!/usr/bin/env bash

sudo apt-get install supervisor
cp /home/mlprior/git_app/config_files/supervisor/mlprior_celery.conf /etc/supervisor/conf.d/
cp /home/mlprior/git_app/config_files/supervisor/mlprior_celerybeat.conf /etc/supervisor/conf.d/

touch /var/log/celery/picha_worker.log
touch /var/log/celery/picha_beat.log

sudo supervisorctl reread
sudo supervisorctl update

sudo supervisorctl start pichacelery

sudo supervisorctl status pichacelery