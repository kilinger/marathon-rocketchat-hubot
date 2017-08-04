web: gunicorn hubot.wsgi --preload --log-file -
marathon: python manage.py marathon_monitor
celery: celery -A hubot worker -l info
celery-scheduler: celery -A hubot beat
