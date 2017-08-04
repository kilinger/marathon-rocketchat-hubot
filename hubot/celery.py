# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from celery import Celery
from django.conf import settings

from hubot.settings import read_env
read_env()
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hubot.settings')

app = Celery('hubot')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
