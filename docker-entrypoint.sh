#!/bin/sh

python manage.py migrate
python manage.py runserver ${APP_HOST:-0.0.0.0}:${APP_PORT:-8000}
