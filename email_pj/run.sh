#!/bin/bash
set -e
wait-for-it postgres_db:5432 -t 30
python manage.py makemigrations
python manage.py migrate
python3 manage.py runserver 0.0.0.0:7000
