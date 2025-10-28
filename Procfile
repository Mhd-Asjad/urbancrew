web: cd ecommerce && gunicorn ecommerce.wsgi:application --bind 0.0.0.0:$PORT
release: cd ecommerce && python manage.py migrate