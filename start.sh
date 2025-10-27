#!/bin/bash
python manage.py collectstatic --noinput
gunicorn ecommerce.wsgi