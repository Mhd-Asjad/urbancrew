#!/bin/bash
cd ecommerce
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn ecommerce.wsgi