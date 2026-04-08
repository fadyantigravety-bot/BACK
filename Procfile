release: python manage.py migrate
web: daphne -b 0.0.0.0 -p $PORT config.asgi:application
worker: celery -A config.celery:app worker --loglevel=info
beat: celery -A config.celery:app beat --loglevel=info

ل