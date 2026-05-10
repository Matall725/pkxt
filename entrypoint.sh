#!/bin/sh
set -e

python manage.py migrate --settings=config.settings.prod
python manage.py collectstatic --noinput --settings=config.settings.prod

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
