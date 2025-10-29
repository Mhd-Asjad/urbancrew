release: cd ecommerce && python manage.py migrate && python manage.py collectstatic --noinput
web: cd ecommerce && gunicorn ecommerce.wsgi:application --bind 0.0.0.0:$PORT
